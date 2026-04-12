"""
Celery task queue for background PDF report generation.

Uses WeasyPrint (HTML+CSS → PDF) so the PDF design is fully controllable via CSS.
Redis is used as both broker and result backend (already in docker-compose).

Worker startup (handled by docker-compose):
    celery -A services.pdf_tasks worker --loglevel=info --concurrency=4 -Q pdf
"""

import os
import re
import sys
from datetime import datetime

# Ensure the app root is on the path so that 'models', 'db', etc. resolve
sys.path.insert(0, "/app")

from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ---------------------------------------------------------------------------
# Celery + DB setup (sync — workers are not async)
# ---------------------------------------------------------------------------

REDIS_URL    = os.getenv("REDIS_URL", "redis://redis:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/astronova")
PDF_DIR      = "/app/pdf_output"

celery_app = Celery("astronova_pdf", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_track_started=True,
    worker_max_memory_per_child=500_000,   # restart worker process after 500 MB
    task_acks_late=True,                   # re-queue if worker dies mid-task
)

_engine  = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)
_Session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

# ---------------------------------------------------------------------------
# PDF HTML template builder
# ---------------------------------------------------------------------------

SECTION_META = {
    "yearly_summary":      ("📅", "Годината на кратко"),
    "planetary_positions": ("🪐", "Планетарни позиции и акценти"),
    "life_structure":      ("🏗️", "Как да структурираш живота си"),
    "main_theme":          ("⭐", "Главната тема на годината"),
    "yearly_details":      ("🔭", "Годината в детайли"),
}


def _build_pdf_html(analysis, report) -> str:
    """Render complete PDF HTML from analysis + report records."""
    bd      = analysis.person1_birth_date.strftime("%d.%m.%Y %H:%M") if analysis.person1_birth_date else "—"
    birth_date = analysis.person1_birth_date.strftime("%d.%m.%Y") if analysis.person1_birth_date else "—"
    birth_time = analysis.person1_birth_date.strftime("%H:%M") if analysis.person1_birth_date else "—"
    year    = analysis.solar_return_year or "—"
    try:
        year_range = f"{int(year)}-{int(year)+1}"
    except (ValueError, TypeError):
        year_range = str(year)
    name    = analysis.person1_name or "—"
    first_name = name.split()[0] if name != "—" else name
    place   = analysis.person1_birth_place or "—"
    bloc    = analysis.person1_birthday_location or "—"
    variant = analysis.variant_title or analysis.product_title or "Соларен анализ"
    today   = datetime.now().strftime("%d.%m.%Y")

    sections_html = ""
    for key, (icon, label) in SECTION_META.items():
        content = getattr(report, key, None) if report else None
        if not content or not content.strip():
            continue
        sections_html += f"""
        <div class="section">
            <h2 class="section-title"><span class="section-icon">{icon}</span>{label}</h2>
            <div class="section-rule"></div>
            <div class="section-body">{content}</div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="bg">
<head>
<meta charset="UTF-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,600;0,700;1,400&display=swap">
<style>
  /* ── FONTS ── */
  @font-face {{
    font-family: 'DejaVu Serif';
    src: local('DejaVu Serif'), local('DejaVuSerif');
  }}

  :root {{
    --gold:   #C9A84C;
    --dark:   #0e0e1a;
    --text:   #1e1e2e;
    --muted:  #6b6b80;
    --accent: #6B4FA8;
    --light:  #f7f5ff;
    --rule:   #e0dce8;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  @page {{
    size: A4;
    margin: 55mm 20mm 18mm 20mm;
    @bottom-left {{
      content: "www.astronovabg.com";
      font-family: 'EB Garamond', 'DejaVu Serif', serif;
      font-size: 9pt;
      color: rgba(255,255,255,0.6);
      vertical-align: middle;
    }}
    @bottom-right {{
      content: "2026";
      font-family: 'EB Garamond', 'DejaVu Serif', serif;
      font-size: 9pt;
      color: rgba(255,255,255,0.6);
      vertical-align: middle;
    }}
  }}
  @page :first {{
    margin: 0;
    @bottom-left {{ content: none; }}
    @bottom-right {{ content: none; }}
  }}
  @page intro {{
    margin: 0;
    @bottom-left {{ content: none; }}
    @bottom-right {{ content: none; }}
  }}

  body {{
    font-family: 'EB Garamond', 'DejaVu Serif', serif;
    font-size: 16pt;
    line-height: 1.85;
    color: #ffffff;
    background: transparent;
    padding: 0;
    margin: 0;
  }}

  .content-wrap {{
    padding: 0;
  }}
  .content-bg {{
    position: fixed;
    top: -55mm;
    left: -20mm;
    width: 210mm;
    height: 297mm;
    object-fit: cover;
    object-position: center;
    z-index: -1;
  }}

  /* ──────────────────────── COVER PAGE ──────────────────────── */
  .cover {{
    width: 210mm;
    height: 297mm;
    position: relative;
    page-break-after: always;
    overflow: hidden;
  }}
  .cover-bg {{
    position: absolute;
    top: 0;
    left: 0;
    width: 210mm;
    height: 297mm;
  }}
  .cover-text {{
    position: absolute;
    left: 0;
    right: 0;
    bottom: 45mm;
    text-align: center;
    padding-left: 4mm;
  }}
  .cover-solar-title {{
    font-family: 'EB Garamond', 'DejaVu Serif', serif;
    font-size: 44pt;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    white-space: nowrap;
    color: #fce6e1;
    margin-bottom: 0;
  }}
  .cover-year-range {{
    font-family: 'EB Garamond', 'DejaVu Serif', serif;
    font-size: 30pt;
    font-weight: 600;
    letter-spacing: 3px;
    color: #fce6e1;
    margin-bottom: 7mm;
  }}
  .cover-na {{
    font-family: 'EB Garamond', 'DejaVu Serif', serif;
    font-size: 13pt;
    font-style: italic;
    letter-spacing: 2px;
    color: #fce6e1;
    margin-bottom: 5mm;
  }}
  .cover-client-name {{
    font-family: 'EB Garamond', 'DejaVu Serif', serif;
    font-size: 34pt;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #f0c0b7;
  }}
  .cover-logo {{
    position: absolute;
    bottom: 10mm;
    left: 0;
    right: 0;
    margin: 0 auto;
    display: block;
    width: 38mm;
    height: auto;
  }}

  /* ──────────────────────── INTRO PAGE ──────────────────────── */
  .intro-page {{
    page: intro;
    width: 210mm;
    height: 297mm;
    position: relative;
    page-break-after: always;
    overflow: hidden;
  }}
  .intro-bg {{
    position: absolute;
    top: 0;
    left: 0;
    width: 210mm;
    height: 297mm;
  }}
  .intro-content {{
    position: absolute;
    top: 50mm;
    left: 28mm;
    right: 28mm;
  }}
  .intro-table {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 9mm;
  }}
  .intro-table td {{
    border: none;
    padding: 0.4mm 2mm;
    vertical-align: top;
  }}
  .col-label {{
    font-family: 'EB Garamond', 'DejaVu Serif', serif;
    font-size: 19pt;
    font-style: italic;
    font-weight: 700;
    color: #fce6e1;
    text-align: left;
    width: 52%;
  }}
  .col-value {{
    font-family: 'EB Garamond', 'DejaVu Serif', serif;
    font-size: 19pt;
    color: #f0c0b7;
    text-align: left;
  }}
  .intro-text {{
    font-family: 'EB Garamond', 'DejaVu Serif', serif;
    font-size: 12pt;
    font-weight: 700;
    color: #fce6e1;
    line-height: 1.85;
    text-align: center;
  }}
  .intro-text p {{
    margin-bottom: 3mm;
    text-align: justify;
  }}

  /* ──────────────────────── SECTIONS ──────────────────────── */
  .section {{
    margin-bottom: 10mm;
  }}
  .section-title {{
    font-family: 'EB Garamond', 'DejaVu Serif', serif;
    font-size: 18pt;
    font-weight: 700;
    color: #ffffff;
    text-transform: uppercase;
    text-align: center;
    padding-bottom: 2mm;
    margin-bottom: 2mm;
    margin-top: 8mm;
    display: block;
  }}
  .section-rule {{
    width: 50mm;
    margin: 0 auto 5mm;
    border-top: 1.5pt solid rgba(255,255,255,0.4);
  }}
  .section-icon {{
    font-size: 14pt;
  }}
  .section-body {{
    font-family: 'EB Garamond', 'DejaVu Serif', serif;
    font-size: 16pt;
    line-height: 1.9;
    color: #ffffff;
  }}
  .section-body p {{
    margin-bottom: 3.5mm;
    text-align: justify;
  }}
  .section-body ul, .section-body ol {{
    margin: 2mm 0 3.5mm 6mm;
  }}
  .section-body li {{
    margin-bottom: 1.5mm;
  }}
  .section-body strong, .section-body b {{
    color: #ffffff;
    font-weight: 700;
  }}

  /* ──────────────────────── FOOTER NOTE ──────────────────────── */
  .report-footer {{
    margin-top: 16mm;
    padding-top: 4mm;
    border-top: .5pt solid rgba(255,255,255,0.3);
    font-family: 'EB Garamond', 'DejaVu Serif', serif;
    font-size: 10pt;
    color: rgba(255,255,255,0.7);
    text-align: center;
  }}

  /* ──────────────────────── FINAL PAGE ──────────────────────── */
  .final-page {{
    page: intro;
    width: 210mm;
    height: 297mm;
    position: relative;
    page-break-before: always;
    overflow: hidden;
  }}
  .final-bg {{
    position: absolute;
    top: 0;
    left: 0;
    width: 210mm;
    height: 297mm;
    object-fit: cover;
    object-position: center;
  }}
  .final-content {{
    position: absolute;
    top: 120mm;
    left: 24mm;
    right: 24mm;
  }}
  .final-content p {{
    font-family: 'EB Garamond', 'DejaVu Serif', serif;
    font-size: 13pt;
    font-weight: 700;
    color: #fce6e1;
    line-height: 1.85;
    text-align: left;
    margin-bottom: 3mm;
  }}
  .final-content .final-signature {{
    margin-top: 6mm;
    font-style: italic;
  }}
</style>
</head>
<body>

<!-- ═══════════════════════ COVER ═══════════════════════ -->
<div class="cover">
  <img class="cover-bg" src="https://cdn.shopify.com/s/files/1/0967/1707/8911/files/ChatGPT_Image_Mar_24_2026_11_10_04_PM.png?v=1774449158" />
  <div class="cover-text">
    <div class="cover-solar-title">СОЛАРНА КАРТА</div>
    <div class="cover-year-range">{year_range}</div>
    <div class="cover-na">на</div>
    <div class="cover-client-name">{name}</div>
  </div>
  <img class="cover-logo" src="https://cdn.shopify.com/s/files/1/0967/1707/8911/files/symbols_nw_path151_logo-title.png?v=1766310535" />
</div>

<!-- ═══════════════════════ INTRO PAGE ═══════════════════════ -->
<div class="intro-page">
  <img class="intro-bg" src="https://cdn.shopify.com/s/files/1/0967/1707/8911/files/ChatGPT_Image_Mar_24_2026_11_15_43_PM.png?v=1774449158" />
  <div class="intro-content">
    <table class="intro-table">
      <tr>
        <td class="col-label">Име</td>
        <td class="col-value">{name}</td>
      </tr>
      <tr>
        <td class="col-label">Рождена дата</td>
        <td class="col-value">{birth_date}</td>
      </tr>
      <tr>
        <td class="col-label">Час на раждане</td>
        <td class="col-value">{birth_time}</td>
      </tr>
      <tr>
        <td class="col-label">Място на раждане</td>
        <td class="col-value">{place}</td>
      </tr>
      <tr>
        <td class="col-label">Рожден ден (локация)</td>
        <td class="col-value">{bloc}</td>
      </tr>
    </table>
    <div class="intro-text">
      <p>Здравей, {first_name},<br>Добре дошла в своята соларна карта.</p>
      <p>Това не е просто анализ. Това е твоята лична карта за една година, в която ще се пренареждат приоритети, ще се взимат важни решения и ще се отварят нови възможности.</p>
      <p>Соларната карта показва каква енергия носи годината специално за теб — къде ще се движиш по-лесно, къде ще бъдеш предизвикана и къде имаш най-голям потенциал за растеж.</p>
      <p>В този анализ ще откриеш:<br>
      — кои области от живота ти ще бъдат най-активни;<br>
      — къде си струва да вложиш усилия и внимание;<br>
      — кои моменти изискват повече осъзнатост и търпение;<br>
      — как да използваш тази година по най-добрия начин за себе си.</p>
      <p>Тази карта не е за това да ти каже какво ще се случи. Тя е тук, за да ти покаже как да преминеш през годината с повече яснота, увереност и посока.</p>
      <p>Позволи си да я прочетеш бавно и да чуеш какво всъщност ти казва.</p>
    </div>
  </div>
</div>
<img class="content-bg" src="file:///app/static/content-bg.png" />
<div class="content-wrap">
{sections_html}

<div class="report-footer">
  AstroNova &nbsp;·&nbsp; Персонализиран соларен анализ за <strong>{name}</strong> &nbsp;·&nbsp; {year} г.
</div>
</div>

<!-- ═══════════════════════ FINAL PAGE ═══════════════════════ -->
<div class="final-page">
  <img class="final-bg" src="https://cdn.shopify.com/s/files/1/0967/1707/8911/files/ChatGPT_Image_Mar_25_2026_12_24_36_PM.png?v=1774449158" />
  <div class="final-content">
    <p>Скъпа, {first_name},</p>
    <p>благодаря ти, че ми позволи да погледна в твоята астрологична карта!</p>
    <p>Надявам се този анализ да ти е дал яснота, увереност и усещане за посока.</p>
    <p>Помни: звездите не вземат решенията вместо теб — те осветяват пътя,<br>
    за да вървиш по него осъзнато и със сила. 2026 е година на Слънцето и<br>
    новото начало. Година, в която знанието за точния момент прави<br>
    разликата между съмнение и уверен избор.</p>
    <p>Ако този анализ ти е бил полезен и резонира с теб, ще се радвам да го<br>
    споделиш с хора, които обичаш. Персоналните анализи и прогнози са<br>
    прекрасен подарък — за приятел, партньор или близък човек, който също е<br>
    на прага на важен избор. За още персонални прогнози, анализи за 2026 или<br>
    лични консултации, можеш да направиш поръчка директно на<br>
    www.astronovabg.com.</p>
    <p>Благодаря ти за доверието!</p>
    <p>Нека Слънцето на 2026 осветява пътя ти ясно, смело и с увереност!</p>
    <p class="final-signature">С уважение,<br>Адриана Авиор</p>
  </div>
</div>

</body>
</html>"""


# ---------------------------------------------------------------------------
# Celery task
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=2, default_retry_delay=15, queue="pdf")
def generate_pdf_task(self, job_id: int):
    """
    Background task: load analysis+report from DB, render PDF with WeasyPrint,
    save to /app/pdf_output/, update PdfJob status.
    """
    # Lazy imports so the module loads fast and avoids circular deps at import time
    from models.shopify_order import PdfJob, PdfJobStatus, Analysis, SolarReturnReport, ShopifyOrder  # noqa
    from weasyprint import HTML  # noqa

    db  = _Session()
    job = None
    try:
        job = db.query(PdfJob).filter(PdfJob.id == job_id).first()
        if not job:
            return  # job was deleted — nothing to do

        job.status = PdfJobStatus.PROCESSING
        db.commit()

        analysis = db.query(Analysis).filter(Analysis.id == job.analysis_id).first()
        if not analysis:
            raise RuntimeError(f"Analysis {job.analysis_id} not found")

        report = (
            db.query(SolarReturnReport)
            .filter(SolarReturnReport.analysis_id == job.analysis_id)
            .first()
        )

        html_content = _build_pdf_html(analysis, report)

        os.makedirs(PDF_DIR, exist_ok=True)
        safe_name = re.sub(r"[^\w\-]", "_", analysis.person1_name or "unknown")
        order = db.query(ShopifyOrder).filter(ShopifyOrder.id == analysis.order_id).first()
        order_num = re.sub(r"[^\w\-]", "_", str(order.order_number)) if order else str(job.id)
        filename  = f"Astronova_{safe_name}_{order_num}.pdf"
        filepath  = os.path.join(PDF_DIR, filename)

        HTML(string=html_content).write_pdf(filepath)

        job.status    = PdfJobStatus.DONE
        job.file_path = filepath
        db.commit()

        # ── Upload to Google Drive (best-effort; does not fail the job) ──
        try:
            from services.google_drive import upload_pdf  # noqa
            drive_id, drive_link = upload_pdf(filepath, filename)
            job.drive_file_id = drive_id
            job.drive_link    = drive_link
            # Also persist on the analysis so the link is always available
            analysis = db.query(Analysis).filter(Analysis.id == job.analysis_id).first()
            if analysis:
                analysis.drive_link = drive_link
            db.commit()
        except Exception as drive_exc:
            import logging
            logging.getLogger(__name__).warning(
                "Google Drive upload failed for job %s: %s", job_id, drive_exc
            )

    except Exception as exc:
        if job:
            job.status        = PdfJobStatus.FAILED
            job.error_message = str(exc)[:1000]
            db.commit()
        raise self.retry(exc=exc)
    finally:
        db.close()
