import { UserButton } from "@clerk/nextjs";
import { ScaleIcon, ShieldUserIcon } from "lucide-react";


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
      >
        <UserButton.MenuItems>
          <UserButton.Link
            label="Privacy Policy"
            labelIcon={<ShieldUserIcon size={16} />}
            href="/privacy-policy"
          />
        </UserButton.MenuItems>
        <UserButton.MenuItems>
          <UserButton.Link
            label="Legal Notice"
            labelIcon={<ScaleIcon size={16} />}
            href="/legal-notice"
          />
        </UserButton.MenuItems>
      </UserButton>
    </div>
  )
}
