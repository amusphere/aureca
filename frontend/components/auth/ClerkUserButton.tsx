import { UserButton } from "@clerk/nextjs";


export default function ClerkUserButton() {
  return (
    <div className="relative">
      <UserButton
        appearance={{
          elements: {
            userButtonBox: {
              flexDirection: "row-reverse",
            },
            userButtonPopoverCard: {
              pointerEvents: "auto",
              zIndex: "9999",
              position: "fixed",
              touchAction: "manipulation",
            },
            userButtonPopoverActionButton: {
              pointerEvents: "auto",
              touchAction: "manipulation",
              cursor: "pointer",
            },
            userButtonPopoverActionButtonText: {
              pointerEvents: "auto",
              touchAction: "manipulation",
            },
            userButtonPopoverFooter: {
              pointerEvents: "auto",
              touchAction: "manipulation",
            },
            userButtonPopoverActions: {
              pointerEvents: "auto",
              touchAction: "manipulation",
            },
          },
        }}
        showName={true}
      />
    </div>
  )
}
