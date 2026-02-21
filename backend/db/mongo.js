// backend/db/mongo.js
import { MongoClient } from "mongodb";

const uri = process.env.MONGO_URI;
let client;
let clientPromise;

if (!uri) throw new Error("MONGO_URI not set in .env");

if (process.env.NODE_ENV === "development") {
  // Prevent multiple connections during hot reload
  if (!global._mongoClientPromise) {
    client = new MongoClient(uri);
    global._mongoClientPromise = client.connect();
  }
  clientPromise = global._mongoClientPromise;
} else {
  // Production
  client = new MongoClient(uri);
  clientPromise = client.connect();
}

export default clientPromise;