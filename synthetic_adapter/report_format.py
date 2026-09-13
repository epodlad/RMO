"""Presentation only: retain missing numeric report entries without implying zero."""
from html import escape

VALUE_NOTE = "No separate numerical value reported"
TOLERANCE_NOTE = "No separate tolerance reported"
LEGEND = ('<p class="small"><strong>—</strong> means no separate numerical value or '
          'tolerance is reported in this cell. The check status is shown separately. '
          'This does not mean zero, missing plasma input, or that no tolerance was '
          'used internally.</p>')


def cell(value, *, tolerance=False):
    if value is None:
        note = TOLERANCE_NOTE if tolerance else VALUE_NOTE
        return f'<span title="{note}" aria-label="{note}">—</span>'
    return escape(str(value))
