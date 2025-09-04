selector_to_html = {"a[href=\"#key-relationships\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">\ud83d\udcda <strong>Key Relationships</strong><a class=\"headerlink\" href=\"#key-relationships\" title=\"Link to this heading\">\u00b6</a></h2>", "a[href=\"#legend\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">\ud83d\udccb <strong>Legend</strong><a class=\"headerlink\" href=\"#legend\" title=\"Link to this heading\">\u00b6</a></h2>", "a[href=\"#class-inheritance-diagram\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">\ud83d\udcca Class Inheritance Diagram<a class=\"headerlink\" href=\"#class-inheritance-diagram\" title=\"Link to this heading\">\u00b6</a></h1><p>This interactive diagram shows the class hierarchy within the Haive MCP package and its relationships to the core Haive framework.</p>", "a[href=\"#external-references\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">\ud83d\udd17 <strong>External References</strong><a class=\"headerlink\" href=\"#external-references\" title=\"Link to this heading\">\u00b6</a></h2><p>This diagram shows relationships between haive-mcp classes and core Haive framework classes:</p>", "a[href=\"autoapi/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">API Reference<a class=\"headerlink\" href=\"#api-reference\" title=\"Link to this heading\">\u00b6</a></h1><p>This page contains auto-generated API reference documentation <a class=\"footnote-reference brackets\" href=\"#f1\" id=\"id1\" role=\"doc-noteref\"><span class=\"fn-bracket\">[</span>1<span class=\"fn-bracket\">]</span></a>.</p>"}
skip_classes = ["headerlink", "sd-stretched-link", "reference-external"]

window.onload = function () {
    for (const [select, tip_html] of Object.entries(selector_to_html)) {
        const links = document.querySelectorAll(`div.content ${select}`);
        for (const link of links) {
            if (skip_classes.some(c => link.classList.contains(c))) {
                continue;
            }
            link.classList.add('has-tooltip');
            tippy(link, {
                content: tip_html,
                allowHTML: true,
                arrow: true,
                placement: 'auto-start', maxWidth: 600, interactive: true, theme: 'light-border', delay: [200, 100], duration: [200, 100],
                onShow(instance) {MathJax.typesetPromise([instance.popper]).then(() => {});},
            });
        };
    };
    console.log("tippy tips loaded!");
};
