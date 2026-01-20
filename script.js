const form = document.getElementById("topsisForm");
const msg = document.getElementById("msg");

const BACKEND_URL = "https://YOUR-RENDER-APP.onrender.com/topsis";

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  msg.innerText = "Processing...";

  const formData = new FormData(form);

  try {
    const res = await fetch(BACKEND_URL, {
      method: "POST",
      body: formData
    });

    const data = await res.json();
    msg.innerText = data.message;
  } catch (err) {
    msg.innerText = "Error connecting to server";
  }
});
