selector_to_html = {"a[href=\"#multiple-servers-example\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Multiple Servers Example<a class=\"headerlink\" href=\"#multiple-servers-example\" title=\"Link to this heading\">\u00b6</a></h2><p>Working with multiple MCP servers:</p>", "a[href=\"#next-steps\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Next Steps<a class=\"headerlink\" href=\"#next-steps\" title=\"Link to this heading\">\u00b6</a></h2><p>Now that you have a basic setup working:</p>", "a[href=\"#complete-example\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Complete Example<a class=\"headerlink\" href=\"#complete-example\" title=\"Link to this heading\">\u00b6</a></h2><p>Here\u2019s a complete working example:</p>", "a[href=\"#basic-setup\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Basic Setup<a class=\"headerlink\" href=\"#basic-setup\" title=\"Link to this heading\">\u00b6</a></h2>", "a[href=\"#quick-start\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">Quick Start<a class=\"headerlink\" href=\"#quick-start\" title=\"Link to this heading\">\u00b6</a></h1><p>This guide will get you up and running with haive-mcp in 5 minutes.</p>", "a[href=\"#common-issues\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Common Issues<a class=\"headerlink\" href=\"#common-issues\" title=\"Link to this heading\">\u00b6</a></h2><p>For more help, see the <a class=\"reference external\" href=\"troubleshooting.html\">troubleshooting guide</a>.</p>", "a[href=\"#factory-method-approach\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Factory Method Approach<a class=\"headerlink\" href=\"#factory-method-approach\" title=\"Link to this heading\">\u00b6</a></h2><p>For simpler setup, use the factory method:</p>"}
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
