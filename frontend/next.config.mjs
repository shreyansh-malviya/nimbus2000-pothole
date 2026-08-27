/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Annotated frames are pre-baked JPGs in /public; no next/image optimization needed.
  images: { unoptimized: true },
};
export default nextConfig;
