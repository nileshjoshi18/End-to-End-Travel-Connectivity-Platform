import { NextResponse } from "next/server"
import { clientPromise } from "@/lib/mongodb"
import bcrypt from "bcryptjs"

export async function POST(req: Request) {
  const { email, password } = await req.json()

  const client = await clientPromise
  const db = client.db("travelbuddy")

  const existing = await db.collection("users").findOne({ email })

  if (existing) {
    return NextResponse.json(
      { error: "User exists" },
      { status: 400 }
    )
  }

  const hashedPassword = await bcrypt.hash(password, 10)

  await db.collection("users").insertOne({
    email,
    password: hashedPassword,
    provider: "credentials",
    createdAt: new Date()
  })

  return NextResponse.json({ success: true })
}