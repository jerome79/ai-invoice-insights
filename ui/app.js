async function analyze() {
    const fileInput = document.getElementById("fileInput");
    if (!fileInput.files.length) {
        alert("Please select a PDF");
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    const res = await fetch("http://localhost:8080/analyze", {
        method: "POST",
        body: formData
    });

    const data = await res.json();
    document.getElementById("analysisOutput").innerHTML =
        "<pre>" + JSON.stringify(data, null, 2) + "</pre>";
}

async function testMCP() {
    const text = document.getElementById("mcpText").value;

    const res = await fetch("http://localhost:8000/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text })
    });

    const data = await res.json();
    document.getElementById("mcpOutput").innerHTML =
        "<pre>" + JSON.stringify(data, null, 2) + "</pre>";
}
