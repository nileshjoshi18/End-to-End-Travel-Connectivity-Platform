import NextAuth from "next-auth"
import GoogleProvider from "next-auth/providers/google"
import CredentialsProvider from "next-auth/providers/credentials"
import { MongoDBAdapter } from "@next-auth/mongodb-adapter"
import { clientPromise } from "@/lib/mongodb"
import bcrypt from "bcryptjs"
import { MongoClient } from "mongodb"

const handler = NextAuth({
  adapter: MongoDBAdapter(clientPromise),

  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),

    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: {},
        password: {}
      },
      async authorize(credentials) {
        const client = await clientPromise
        const db = client.db("travelbuddy_logininfo")

        const user = await db.collection("users").findOne({
          email: credentials?.email
        })

        if (!user) return null

        const valid = await bcrypt.compare(
          credentials!.password,
          user.password
        )

        if (!valid) return null

        return {
          id: user._id.toString(),
          email: user.email
        }
      }
    })
  ],

  session: {
    strategy: "jwt"
  },

  secret: process.env.NEXTAUTH_SECRET
})

export { handler as GET, handler as POST }