const express = require("express");
const app = express();
const PORT = 3000;

// Root route
app.get("/", (req, res) => {
  res.send("Hello from server");
});

// Start server
app.listen(PORT, () => {
  console.log(`Gateway service listening on port ${PORT}`);
});
