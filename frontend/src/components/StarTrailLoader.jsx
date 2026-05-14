import { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

export default function StarTrailLoader({ onComplete }) {
  const canvasRef = useRef(null);
  const rafRef = useRef(null);
  const startRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const maxR = Math.sqrt(cx * cx + cy * cy) + 80;

    // ~55 stars, well spread, radii from near-zero to past screen corners
    const stars = Array.from({ length: 55 }, () => ({
      radius: 12 + Math.random() ** 0.4 * maxR,
      baseAngle: Math.random() * Math.PI * 2,
      brightness: 0.3 + Math.random() * 0.7,
      width: 0.4 + Math.random() * 0.9,
      // very slow: 0.03–0.08 full turns over the animation
      speed: (0.03 + Math.random() * 0.05) * (Math.random() > 0.5 ? 1 : -1),
    }));

    const DURATION = 2200;
    const TRAIL_ARC = Math.PI * 0.48;

    const draw = (ts) => {
      if (!startRef.current) startRef.current = ts;
      const progress = Math.min((ts - startRef.current) / DURATION, 1);

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      for (const s of stars) {
        const trailLen = TRAIL_ARC * Math.min(progress * 2.5, 1);
        if (trailLen < 0.005) continue;

        const headAngle = s.baseAngle + s.speed * progress * Math.PI * 2;
        const tailAngle = headAngle - Math.sign(s.speed) * trailLen;

        const alpha = s.brightness * Math.min(progress * 3, 1) * 0.35;

        // Single arc stroke per star — fast
        ctx.beginPath();
        ctx.arc(cx, cy, s.radius, tailAngle, headAngle, s.speed < 0);
        ctx.strokeStyle = `rgba(200, 225, 255, ${alpha})`;
        ctx.lineWidth = s.width;
        ctx.stroke();

        // Soft head dot
        const hx = cx + Math.cos(headAngle) * s.radius;
        const hy = cy + Math.sin(headAngle) * s.radius;
        ctx.beginPath();
        ctx.arc(hx, hy, s.width * 1.5, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(230, 242, 255, ${s.brightness * Math.min(progress * 4, 1) * 0.5})`;
        ctx.fill();
      }

      if (progress < 1) {
        rafRef.current = requestAnimationFrame(draw);
      } else {
        setTimeout(() => onComplete?.(), 150);
      }
    };

    rafRef.current = requestAnimationFrame(draw);
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, [onComplete]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      style={{ position: 'absolute', inset: 0, zIndex: 1 }}
    >
      <canvas ref={canvasRef} style={{ position: 'absolute', inset: 0 }} />
    </motion.div>
  );
}
