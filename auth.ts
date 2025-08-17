import express from "express";
import bodyParser from "body-parser";
import mongoose from "mongoose";
import jwt from "jsonwebtoken";

const router = express.Router();
router.use(bodyParser.json());

// User schema and model
const userSchema = new mongoose.Schema({
  email: { type: String, required: true, unique: true },
  password: { type: String, required: true },
});
const User = mongoose.model("User", userSchema);

const JWT_SECRET = process.env.JWT_SECRET || "supersecretkey";


// Signup route
// All signup logic is handled here in the backend
router.post("/signup", async (req, res) => {
  const { email, password } = req.body;
  try {
    const existingUser = await User.findOne({ email });
    if (existingUser) {
      return res.status(400).json({ success: false, message: "Email already registered" });
    }
    const newUser = new User({ email, password });
    await newUser.save();
  // Issue JWT on signup
  const token = jwt.sign({ email }, JWT_SECRET, { expiresIn: "60s" });
    return res.json({ success: true, token });
  } catch (err) {
    return res.status(500).json({ success: false, message: "Server error" });
  }
});

// Login route
// All login logic is handled here in the backend
router.post("/login", async (req, res) => {
  const { email, password } = req.body;
  try {
    const user = await User.findOne({ email });
    if (user && user.password === password) {
      // Issue JWT on login
      const token = jwt.sign({ email }, JWT_SECRET, { expiresIn: "60s" });
      return res.json({ success: true, token });
    }
    return res.status(401).json({ success: false, message: "Invalid credentials" });
  } catch (err) {
    return res.status(500).json({ success: false, message: "Server error" });
  }
});

export default router;
