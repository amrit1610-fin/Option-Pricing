import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Bloomberg Quant Terminal',
  description: 'Institutional Options Pricing Engine',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      {/* We apply the terminal background color directly to the body */}
      <body className="bg-[#000000] text-[#FFB000] m-0 overflow-hidden">
        {children}
      </body>
    </html>
  );
}