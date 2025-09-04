selector_to_html = {"a[href=\"#submodules\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Submodules<a class=\"headerlink\" href=\"#submodules\" title=\"Link to this heading\">\u00b6</a></h2>", "a[href=\"#module-mcp.downloader\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">downloader<a class=\"headerlink\" href=\"#module-mcp.downloader\" title=\"Link to this heading\">\u00b6</a></h1><p>Module exports.</p>", "a[href=\"core/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">core<a class=\"headerlink\" href=\"#module-mcp.downloader.core\" title=\"Link to this heading\">\u00b6</a></h1><p>Core MCP Downloader implementation.</p><p>This module provides the main GeneralMCPDownloader class that orchestrates\nthe downloading, installation, and configuration of MCP servers from various sources.</p>", "a[href=\"installers/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">installers<a class=\"headerlink\" href=\"#module-mcp.downloader.installers\" title=\"Link to this heading\">\u00b6</a></h1><p>Installer plugins for different MCP server types.</p><p>This module provides installer implementations for various installation methods\nincluding NPM, pip, Git, Docker, binary downloads, and more.</p>", "a[href=\"integration/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">integration<a class=\"headerlink\" href=\"#module-mcp.downloader.integration\" title=\"Link to this heading\">\u00b6</a></h1><p>Agent integration for MCP Downloader.</p><p>This module provides integration between the MCP downloader system and Haive agents,\nenabling automatic tool, resource, and prompt discovery from downloaded MCP servers.</p>", "a[href=\"discovery/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">discovery<a class=\"headerlink\" href=\"#module-mcp.downloader.discovery\" title=\"Link to this heading\">\u00b6</a></h1><p>Server discovery module for finding MCP servers from various sources.</p><p>This module provides functionality to discover MCP servers from multiple\nregistries and sources including npm, PyPI, GitHub, and custom registries.</p>", "a[href=\"legacy_core/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">legacy_core<a class=\"headerlink\" href=\"#module-mcp.downloader.legacy_core\" title=\"Link to this heading\">\u00b6</a></h1><p>General MCP Server Downloader - A flexible, configuration-driven approach.</p><p>This script provides a general, extensible system for downloading and configuring\nMCP servers from various sources using configurable installation strategies.</p>", "a[href=\"github_mass_downloader/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">github_mass_downloader<a class=\"headerlink\" href=\"#module-mcp.downloader.github_mass_downloader\" title=\"Link to this heading\">\u00b6</a></h1><p>Download ALL MCP servers from the GitHub resources.</p><p>This script reads all MCP server information from agent_resources/mcp_servers/\nand downloads/installs every single one in an organized manner.</p>", "a[href=\"config/index.html\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">config<a class=\"headerlink\" href=\"#module-mcp.downloader.config\" title=\"Link to this heading\">\u00b6</a></h1><p>Configuration models for MCP Downloader.</p><p>This module defines the configuration models used throughout the MCP downloader\nsystem, including templates, server configurations, and installation methods.</p>"}
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
