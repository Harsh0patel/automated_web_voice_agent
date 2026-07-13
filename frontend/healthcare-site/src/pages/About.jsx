import React from 'react';
import { Link } from 'react-router-dom';
import './About.css';

const values = [
  { icon: '❤️', title: 'Compassion', desc: 'We treat every patient with empathy, dignity, and respect, putting their well-being at the heart of everything we do.' },
  { icon: '⭐', title: 'Excellence', desc: 'We strive for the highest standards in medical care, continuously improving through education and innovation.' },
  { icon: '🤝', title: 'Integrity', desc: 'We uphold the highest ethical standards in all our interactions, building trust through transparency and honesty.' },
  { icon: '🌍', title: 'Community', desc: 'We are committed to serving our community and improving access to quality healthcare for everyone.' },
];

const milestones = [
  { year: '2005', title: 'Foundation', desc: 'MediCare+ was founded by Dr. Robert Mitchell with a vision to provide accessible, high-quality healthcare to the community.' },
  { year: '2009', title: 'First Expansion', desc: 'Opened our second facility to accommodate growing patient demand, adding 50 new beds and advanced diagnostic equipment.' },
  { year: '2014', title: 'Cardiac Center Launch', desc: 'Launched the region\'s most advanced cardiac care center, featuring state-of-the-art catheterization labs.' },
  { year: '2018', title: '100,000 Patients', desc: 'Celebrated treating our 100,000th patient, a milestone that reflects our commitment to community health.' },
  { year: '2021', title: 'Digital Transformation', desc: 'Implemented a fully integrated digital health platform, enabling telemedicine and seamless patient records.' },
  { year: '2024', title: 'Center of Excellence', desc: 'Recognized as a Center of Excellence in Cardiology, Neurology, and Orthopedics by the National Health Board.' },
];

export default function About() {
  return (
    <>
      {/* ========== PAGE HEADER ========== */}
      <section className="page-header">
        <div className="container page-header__inner animate-in">
          <span className="section-tag">About Us</span>
          <h1>Our Story & Mission</h1>
          <p>
            For nearly two decades, MediCare+ has been dedicated to providing compassionate,
            world-class healthcare to our community. Learn more about who we are.
          </p>
        </div>
      </section>

      {/* ========== INTRO ========== */}
      <section className="section about-intro">
        <div className="container">
          <div className="about-intro__grid">
            <div className="about-intro__content animate-in">
              <h2>Dedicated to Your Health & Well-being</h2>
              <p>
                At MediCare+, we believe that everyone deserves access to exceptional healthcare.
                Founded in 2005, we have grown from a small clinic into a comprehensive medical
                center serving over 50,000 patients annually.
              </p>
              <p>
                Our team of 200+ highly skilled physicians, nurses, and healthcare professionals
                work together to provide personalized care using the latest medical advancements
                and technologies.
              </p>
              <Link to="/contact" className="btn btn-primary" style={{ marginTop: '8px' }}>
                Get in Touch
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </Link>
            </div>
            <div className="about-intro__visual animate-in animate-in-delay-2">
              <div className="about-intro__placeholder">
                🏥
                <p>MediCare+ Hospital</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========== VALUES ========== */}
      <section className="section values">
        <div className="container">
          <div className="section-header animate-in">
            <span className="section-tag">Our Values</span>
            <h2>What We Stand For</h2>
            <p>Our core values guide every decision we make and every interaction we have with our patients and community.</p>
          </div>
          <div className="values__grid">
            {values.map((v, i) => (
              <div key={i} className="value-card animate-in" style={{ animationDelay: `${0.1 + i * 0.1}s` }}>
                <div className="value-card__icon">{v.icon}</div>
                <h4>{v.title}</h4>
                <p>{v.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========== TIMELINE ========== */}
      <section className="section timeline-section">
        <div className="container">
          <div className="section-header animate-in">
            <span className="section-tag">Our Journey</span>
            <h2>Milestones Along the Way</h2>
            <p>From our humble beginnings to becoming a leading healthcare provider — a journey of growth and dedication.</p>
          </div>
          <div className="timeline animate-in">
            {milestones.map((m, i) => (
              <div key={i} className="timeline__item">
                <div className="timeline__dot" />
                <div className="timeline__spacer" />
                <div className="timeline__content animate-in" style={{ animationDelay: `${0.1 + i * 0.15}s` }}>
                  <span className="timeline__year">{m.year}</span>
                  <h4>{m.title}</h4>
                  <p>{m.desc}</p>
                </div>
                <div className="timeline__spacer" />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========== CTA ========== */}
      <section className="cta-banner">
        <div className="container">
          <div className="cta-banner__inner animate-in">
            <h2>Want to Know More?</h2>
            <p>We'd love to hear from you. Reach out to us with any questions or to schedule a visit.</p>
            <Link to="/contact" className="btn btn-primary">
              Contact Us
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
