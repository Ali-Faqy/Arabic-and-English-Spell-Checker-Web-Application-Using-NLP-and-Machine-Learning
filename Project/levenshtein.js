document.querySelector("#correctButton").addEventListener("click", function () {
    let inputText = document.querySelector("#inputText").value;
    let inputFile = document.querySelector("#inputFile").files[0];
  
    if (!inputFile) {
      sendInputText(inputText, "");
    } else {
      const reader = new FileReader();
      reader.onload = function (event) {
        let fileContent = event.target.result;
        sendInputText(inputText, fileContent);
      };
      reader.readAsText(inputFile);
    }
  });
  
  
  async function sendInputText(textArea, textFile) {
    try {
      let bodyData;
      if (textArea == "" && textFile == "") {
        alert("You must write text or upload a file.");
        return;
      } else if (textArea != "" && textFile != "") {
        alert("You must write text or upload a file, not both.");
        return;
      }
      else if (textFile != "" && textArea == "") {
        bodyData = JSON.stringify({ textFile });
      } else if(textFile == "" && textArea != "") {
        bodyData = JSON.stringify({ textArea });
      }
  
      const response = await fetch("http://127.0.0.1:5000/PostlevenshteinInputText", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: bodyData,
      });
  
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
  
      console.log("Input sent successfully");
      document.querySelector("#inputText").value = "";
      document.querySelector("#inputFile").value = "";
      fetchData();
    } catch (error) {
      console.error("Error during fetch:", error);
    }
  }
  
  async function fetchData() {
    try {
      let response = await fetch("http://127.0.0.1:5000/getlevenshteinText");
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      const data = await response.json();
      console.log("Data received:", data);
  
      displayReceivedText(data);
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  }

function displayReceivedText(outputText) {
    const tableBody = document.querySelector("#outputTableBody");
    let htmlContent = "";
    if (outputText == ""){
         alert("لا يوجد اخطاء في الجملة.");
         return;
    }

    outputText.forEach((item, index) => {
        htmlContent += createTableRow(item, index);
    });

    tableBody.innerHTML = htmlContent;
}

function createTableRow(item, index) {
    return `
        <tr>
            <td>${item.replace(/\n/g, "<br>")}</td>
            <td>
                <i class="fa-solid fa-download" style="cursor: pointer;" onclick="downloadTextAsFile('${item}')"></i>
            </td>
        </tr>`;
}
  
function downloadTextAsFile(textContent) {
    const blob = new Blob([textContent], { type: "text/plain" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.style.display = "none";
    a.href = url;
    a.download = "Text.txt";
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
  }
