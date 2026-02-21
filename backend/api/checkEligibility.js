import clientPromise from "../db/mongo";

export default async function handler(req, res) {
  const client = await clientPromise;
  const db = client.db("foodnav");

  const programs = await db.collection("program_rules").find({}).toArray();

  res.status(200).json({ programs });
}