
import express from "express";
import mongoose from "mongoose";
import authRouter from "./auth";
import dotenv from "dotenv";
import cors from "cors";
dotenv.config();

const app = express();
const PORT = process.env.PORT || 4000;
const MONGO_URI = process.env.MONGO_URI;
app.use(cors({
  origin: ["https://chatbot-ui-frontend.vercel.app"], // replace with your actual Vercel frontend URL
  credentials: true
}));
app.use(express.json());
app.use("/api", authRouter);

if (!MONGO_URI) {
  throw new Error("MONGO_URI environment variable is not defined. Please set it in your .env file.");
}

mongoose.connect(MONGO_URI)
  .then(() => {
    console.log("MongoDB Atlas connected");
    app.listen(PORT, () => {
      console.log(`Server running on port ${PORT}`);
    });
  })
  .catch((err) => {
    console.error("MongoDB connection error:", err);
  });
