// DOM Elements
const form = document.getElementById("topsisForm");
const fileInput = document.getElementById("fileInput");
const fileNameDisplay = document.getElementById("fileName");
const weightsInput = document.getElementById("weightsInput");
const impactsInput = document.getElementById("impactsInput");
const emailInput = document.getElementById("emailInput");
const submitBtn = document.getElementById("submitBtn");
const messageBox = document.getElementById("messageBox");
const msg = document.getElementById("msg");

// Error displays
const weightsError = document.getElementById("weightsError");
const impactsError = document.getElementById("impactsError");
const emailError = document.getElementById("emailError");

// Backend URL - UPDATE THIS with your Render backend URL after deployment
// For local development: "http://localhost:5000/topsis"
// For production: "https://your-app-name.onrender.com/topsis"
const BACKEND_URL = "https://topsis-backend.onrender.com/topsis";

// File input display update
fileInput.addEventListener("change", (e) => {
  const file = e.target.files[0];
  if (file) {
    fileNameDisplay.textContent = file.name;
    fileNameDisplay.classList.add("has-file");
  } else {
    fileNameDisplay.textContent = "Browse File....";
    fileNameDisplay.classList.remove("has-file");
  }
});

// Validation functions
function validateWeights(weights) {
  if (!weights.trim()) return "Weights are required";
  const parts = weights.split(",").map(w => w.trim());
  for (const part of parts) {
    if (isNaN(parseFloat(part)) || part === "") {
      return "Weights must be comma-separated numeric values";
    }
  }
  return null;
}

function validateImpacts(impacts) {
  if (!impacts.trim()) return "Impacts are required";
  const parts = impacts.split(",").map(i => i.trim());
  for (const part of parts) {
    if (part !== "+" && part !== "-") {
      return "Impacts must be comma-separated + or - values";
    }
  }
  return null;
}

function validateWeightsImpactsCount(weights, impacts) {
  const weightsCount = weights.split(",").length;
  const impactsCount = impacts.split(",").length;
  if (weightsCount !== impactsCount) {
    return `Number of weights (${weightsCount}) must equal number of impacts (${impactsCount})`;
  }
  return null;
}

function validateEmail(email) {
  if (!email.trim()) return "Email is required";
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    return "Please enter a valid email address";
  }
  return null;
}

// Real-time validation
weightsInput.addEventListener("blur", () => {
  const error = validateWeights(weightsInput.value);
  weightsError.textContent = error || "";
  weightsInput.classList.toggle("invalid", !!error);
});

impactsInput.addEventListener("blur", () => {
  const error = validateImpacts(impactsInput.value);
  impactsError.textContent = error || "";
  impactsInput.classList.toggle("invalid", !!error);
  
  // Also check count match
  if (!error && weightsInput.value) {
    const countError = validateWeightsImpactsCount(weightsInput.value, impactsInput.value);
    if (countError) {
      impactsError.textContent = countError;
      impactsInput.classList.add("invalid");
    }
  }
});

emailInput.addEventListener("blur", () => {
  const error = validateEmail(emailInput.value);
  emailError.textContent = error || "";
  emailInput.classList.toggle("invalid", !!error);
});

// Show message
function showMessage(text, type = "info") {
  msg.textContent = text;
  messageBox.className = "message-box show " + type;
}

function hideMessage() {
  messageBox.className = "message-box";
}

function setLoading(loading) {
  submitBtn.classList.toggle("loading", loading);
  submitBtn.disabled = loading;
}

// Form submission
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  hideMessage();

  // Validate all fields
  const weightsErr = validateWeights(weightsInput.value);
  const impactsErr = validateImpacts(impactsInput.value);
  const emailErr = validateEmail(emailInput.value);
  const countErr = validateWeightsImpactsCount(weightsInput.value, impactsInput.value);

  // Show errors
  weightsError.textContent = weightsErr || "";
  weightsInput.classList.toggle("invalid", !!weightsErr);
  
  impactsError.textContent = impactsErr || countErr || "";
  impactsInput.classList.toggle("invalid", !!(impactsErr || countErr));
  
  emailError.textContent = emailErr || "";
  emailInput.classList.toggle("invalid", !!emailErr);

  if (weightsErr || impactsErr || emailErr || countErr) {
    showMessage("Please fix the errors above", "error");
    return;
  }

  // Check file
  if (!fileInput.files[0]) {
    showMessage("Please select a CSV file", "error");
    return;
  }

  setLoading(true);
  showMessage("Processing your request...", "info");

  const formData = new FormData(form);

  try {
    const res = await fetch(BACKEND_URL, {
      method: "POST",
      body: formData
    });

    const data = await res.json();

    if (res.ok) {
      showMessage(data.message || "TOPSIS analysis completed! Check your email for results.", "success");
      form.reset();
      fileNameDisplay.textContent = "Browse File....";
      fileNameDisplay.classList.remove("has-file");
    } else {
      showMessage(data.message || "An error occurred", "error");
    }
  } catch (err) {
    console.error("Error:", err);
    showMessage("Error connecting to server. Please ensure the backend is running.", "error");
  } finally {
    setLoading(false);
  }
});
