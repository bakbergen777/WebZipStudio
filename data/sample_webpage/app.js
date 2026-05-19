// WebZip Studio sample script.
// Demonstrates a tiny single-file demo that the compression pipeline can
// digest just like any production webpage.

(function () {
    "use strict";

    const features = [
        { name: "lossless-text", description: "LZ77 + Huffman pipeline" },
        { name: "controllable-images", description: "JPEG/PNG quality presets" },
        { name: "data-structures", description: "hashmap, heap, tree, queue, set" },
        { name: "fair-comparison", description: "vs gzip and ZIP_DEFLATED" },
        { name: "incremental", description: "skip unchanged files via SHA-256" },
    ];

    function buildFeatureSummary(items) {
        return items
            .map(function (item) { return item.name + ": " + item.description; })
            .join("\n");
    }

    function attachCtaHandler() {
        const cta = document.querySelector(".hero .cta");
        if (!cta) return;
        cta.addEventListener("click", function (event) {
            event.preventDefault();
            const target = document.getElementById("features");
            if (target) {
                target.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        attachCtaHandler();
        if (window.console) {
            console.info("WebZip Studio sample page");
            console.info(buildFeatureSummary(features));
        }
    });
})();
