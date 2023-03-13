from goodreads_export.templates import DEFAULT_EMBEDDED_TEMPLATE, TemplatesLoader


def test_templates_load_embeded():
    templates = TemplatesLoader().load(templates_name=DEFAULT_EMBEDDED_TEMPLATE)
    assert templates.series and templates.book and templates.author and templates.name
