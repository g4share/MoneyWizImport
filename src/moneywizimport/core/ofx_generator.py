from datetime import datetime
from pathlib import Path

from jinja2 import ChoiceLoader, Environment, FileSystemLoader, PackageLoader, select_autoescape

from moneywizimport.model.ofx_models import OfxReport


def _build_template_loader() -> ChoiceLoader | FileSystemLoader | PackageLoader:
    """Create a loader that works both from the repo and installed package."""

    repo_templates = Path(__file__).resolve().parents[1] / "templates" / "ofx"
    loaders: list[FileSystemLoader | PackageLoader] = []

    if repo_templates.is_dir():
        loaders.append(FileSystemLoader(repo_templates))

    loaders.append(PackageLoader("moneywizimport", "templates/ofx"))

    return ChoiceLoader(loaders) if len(loaders) > 1 else loaders[0]


# Configure Jinja2 environment
env = Environment(
    loader=_build_template_loader(),
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
