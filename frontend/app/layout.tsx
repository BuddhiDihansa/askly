import "./globals.css";

export const metadata = {
  title: "ASKLY — Personalized Learning AI",
  description: "An AI-powered personalized learning workspace.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
