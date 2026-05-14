import { useEffect, useRef } from 'react';
import { gsap } from 'gsap';

export default function GalaxyBackground({ variant = 'chat' }) {
  const canvasRef = useRef(null);
  const nebulaRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    const starCount = variant === 'login' ? 260 : 180;
    const stars = Array.from({ length: starCount }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      r: Math.random() < 0.15 ? 1.5 : 1,
      o: 0.05 + Math.random() * 0.35,
    }));

    let shootingStars = [];
    let lastShoot = 0;

    function spawnShootingStar() {
      shootingStars.push({
        x: Math.random() * canvas.width * 1.3 - canvas.width * 0.15,
        y: Math.random() * canvas.height * 0.6,
        vx: -(2.5 + Math.random() * 3),
        vy: 0.8 + Math.random() * 1.2,
        life: 1,
        decay: 0.018 + Math.random() * 0.012,
        length: 80 + Math.random() * 80,
        blue: Math.random() < 0.3,
      });
    }

    let raf;
    let t = 0;

    function draw(now) {
      raf = requestAnimationFrame(draw);
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      t += 0.005;

      // Static stars
      stars.forEach(s => {
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255,255,255,${s.o})`;
        ctx.fill();
      });

      // Shooting stars
      if (now - lastShoot > 2000 + Math.random() * 2500) {
        spawnShootingStar();
        lastShoot = now;
      }

      shootingStars = shootingStars.filter(ss => ss.life > 0);
      shootingStars.forEach(ss => {
        const grad = ctx.createLinearGradient(
          ss.x, ss.y,
          ss.x + ss.vx * (ss.length / 3), ss.y + ss.vy * (ss.length / 3)
        );
        const col = ss.blue ? '200,220,255' : '255,255,255';
        grad.addColorStop(0, `rgba(${col},${ss.life * 0.85})`);
        grad.addColorStop(1, `rgba(${col},0)`);
        ctx.beginPath();
        ctx.moveTo(ss.x, ss.y);
        ctx.lineTo(ss.x + ss.vx * (ss.length / 3), ss.y + ss.vy * (ss.length / 3));
        ctx.strokeStyle = grad;
        ctx.lineWidth = ss.blue ? 1 : 1.2;
        ctx.stroke();
        ss.x += ss.vx;
        ss.y += ss.vy;
        ss.life -= ss.decay;
      });
    }

    raf = requestAnimationFrame(draw);

    // Nebula drift (chat only)
    if (variant === 'chat' && nebulaRef.current) {
      const el = nebulaRef.current;
      const drift = () => {
        const startX = Math.random() * window.innerWidth;
        const startY = Math.random() * window.innerHeight;
        const endX = startX + (Math.random() - 0.5) * 400;
        const endY = startY + (Math.random() - 0.5) * 300;
        const gap = 8000 + Math.random() * 8000;
        const travel = 14000 + Math.random() * 6000;

        gsap.timeline({
          onComplete: () => {
            setTimeout(drift, gap);
          }
        })
          .set(el, { left: startX, top: startY, opacity: 0 })
          .to(el, { opacity: 1, duration: 3, ease: 'power1.inOut' })
          .to(el, { left: endX, top: endY, duration: travel / 1000, ease: 'none' }, 0)
          .to(el, { opacity: 0, duration: 4, ease: 'power1.inOut' }, `-=4`);
      };

      const initialDelay = setTimeout(drift, 2000);
      return () => {
        cancelAnimationFrame(raf);
        window.removeEventListener('resize', resize);
        clearTimeout(initialDelay);
      };
    }

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', resize);
    };
  }, [variant]);

  return (
    <>
      <canvas
        ref={canvasRef}
        style={{
          position: 'fixed',
          inset: 0,
          pointerEvents: 'none',
          zIndex: 0,
          opacity: 1,
        }}
      />
      {variant === 'chat' && (
        <div
          ref={nebulaRef}
          style={{
            position: 'fixed',
            width: 800,
            height: 800,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(10,22,40,0.55) 0%, rgba(200,220,255,0.015) 40%, transparent 70%)',
            filter: 'blur(80px)',
            pointerEvents: 'none',
            zIndex: 0,
            transform: 'translate(-50%, -50%)',
            opacity: 0,
          }}
        />
      )}
    </>
  );
}
