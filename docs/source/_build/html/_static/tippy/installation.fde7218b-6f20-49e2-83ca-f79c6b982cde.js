selector_to_html = {"a[href=\"#installation\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">Installation<a class=\"headerlink\" href=\"#installation\" title=\"Link to this heading\">\u00b6</a></h1><h2>Installing haive-mcp<a class=\"headerlink\" href=\"#installing-haive-mcp\" title=\"Link to this heading\">\u00b6</a></h2><p>The haive-mcp package is part of the Haive framework. You can install it using Poetry:</p>", "a[href=\"#verification\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Verification<a class=\"headerlink\" href=\"#verification\" title=\"Link to this heading\">\u00b6</a></h2><p>Verify your installation:</p>", "a[href=\"#development-installation\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Development Installation<a class=\"headerlink\" href=\"#development-installation\" title=\"Link to this heading\">\u00b6</a></h2><p>For development, clone the repository and install in editable mode:</p>", "a[href=\"#optional-dependencies\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Optional Dependencies<a class=\"headerlink\" href=\"#optional-dependencies\" title=\"Link to this heading\">\u00b6</a></h2><p>For full functionality, install these optional dependencies:</p>", "a[href=\"#mcp-server-installation\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">MCP Server Installation<a class=\"headerlink\" href=\"#mcp-server-installation\" title=\"Link to this heading\">\u00b6</a></h2><p>Many MCP servers are available as npm packages. Install them globally:</p>", "a[href=\"#installing-haive-mcp\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Installing haive-mcp<a class=\"headerlink\" href=\"#installing-haive-mcp\" title=\"Link to this heading\">\u00b6</a></h2><p>The haive-mcp package is part of the Haive framework. You can install it using Poetry:</p>", "a[href=\"#common-issues\"]": "<h3 class=\"tippy-header\" style=\"margin-top: 0;\">Common Issues<a class=\"headerlink\" href=\"#common-issues\" title=\"Link to this heading\">\u00b6</a></h3>", "a[href=\"#getting-help\"]": "<h3 class=\"tippy-header\" style=\"margin-top: 0;\">Getting Help<a class=\"headerlink\" href=\"#getting-help\" title=\"Link to this heading\">\u00b6</a></h3><p>If you encounter issues:</p>", "a[href=\"examples.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">Examples<a class=\"headerlink\" href=\"#examples\" title=\"Link to this heading\">\u00b6</a></h1><p>Comprehensive examples demonstrating haive-mcp capabilities with 1900+ MCP servers.</p>", "a[href=\"#troubleshooting\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Troubleshooting<a class=\"headerlink\" href=\"#troubleshooting\" title=\"Link to this heading\">\u00b6</a></h2><h3>Common Issues<a class=\"headerlink\" href=\"#common-issues\" title=\"Link to this heading\">\u00b6</a></h3>", "a[href=\"#prerequisites\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Prerequisites<a class=\"headerlink\" href=\"#prerequisites\" title=\"Link to this heading\">\u00b6</a></h2><p>Before using haive-mcp, you\u2019ll need:</p>"}
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
