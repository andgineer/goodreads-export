from goodreads_export.templates import Templates


def test_templates_load_embeded():
    templates = Templates()
    assert templates.templates
