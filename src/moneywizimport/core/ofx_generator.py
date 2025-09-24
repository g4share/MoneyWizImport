from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

from moneywizimport.model.ofx_models import OfxReport, Transaction


# Configure Jinja2 environment
env = Environment(
    loader=FileSystemLoader("src/templates/ofx"),
    autoescape=select_autoescape(disabled_extensions=("j2",))
)


def generate_ofx_file(ofx_reports: list[OfxReport]) -> str:
    """Render OFX file from reports using Jinja2 templates."""

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # Load templates
    header_tpl = env.get_template("header.j2")
    transaction_tpl = env.get_template("transaction.j2")
    provider_tpl = env.get_template("provider.j2")
    footer_tpl = env.get_template("footer.j2")

    # Render header
    parts: list[str] = [header_tpl.render(timestamp=timestamp)]

    # Render reports
    for idx, report in enumerate(ofx_reports, start=1):
        transactions = "\n".join(
            transaction_tpl.render(
                transaction=transaction
            )
            for i, transaction in enumerate(report.transactions, start=1)
        )

        parts.append(
            provider_tpl.render(
                index=idx,
                report=report,
                transactions=transactions,
            )
        )

    # Render footer
    parts.append(footer_tpl.render())

    return "\n".join(parts)
