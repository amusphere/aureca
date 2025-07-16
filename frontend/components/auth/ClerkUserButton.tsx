import { UserButton } from "@clerk/nextjs";


export default function ClerkUserButton() {
  return (
    <UserButton appearance={{
      elements: {
        userButtonBox: {
          flexDirection: "row-reverse",
        },
      },
    }} showName={true} />
  )
}
