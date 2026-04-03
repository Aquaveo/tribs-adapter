from typing import Any

from jinja2 import Environment, PackageLoader


def _finalize(val: Any) -> Any:
    if val is None:
        return ""
    return val


_env = Environment(
    loader=PackageLoader('tribs_adapter'),
    finalize=_finalize,
)


def render(template: str, context: dict) -> str:
    """Render given template with given context.

        Args:
            template: Name/path to the template to render.
            context: Context variables to render template with.

        Returns:
            Rendered template as string.
    """
    template = _env.get_template(template)
    return template.render(**context)
