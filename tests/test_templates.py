from goodreads_export.templates import DEFAULT_EMBEDDED_TEMPLATE, Templates


def test_templates_load_embeded():
    templates = Templates(templates_name=DEFAULT_EMBEDDED_TEMPLATE)
    assert templates.templates
