import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './Insurance.css';

const plans = [
  {
    name: 'Essential',
    price: '$149',
    period: '/month',
    desc: 'Basic coverage for individuals and families looking for affordable healthcare.',
    popular: false,
    features: [
      'Primary care visits',
      'Emergency room coverage',
      'Prescription drug discount',
      'Annual health screening',
      'Telemedicine access',
    ],
  },
  {
    name: 'Premium',
    price: '$299',
    period: '/month',
    desc: 'Comprehensive coverage with enhanced benefits and lower deductibles.',
    popular: true,
    features: [
      'Everything in Essential',
      'Specialist visits covered',
      'Hospitalization coverage',
      'Maternity & newborn care',
      'Mental health services',
      'Dental & vision add-on',
    ],
  },
  {
    name: 'Family',
    price: '$499',
    period: '/month',
    desc: 'Complete family coverage for up to 6 members with maximum benefits.',
    popular: false,
    features: [
      'Everything in Premium',
      'Covers up to 6 members',
      'Pediatric dental & vision',
      'Wellness program access',
      'Health coaching',
      'Prescription coverage',
      'No deductible option',
    ],
  },
];

const faqs = [
  { q: 'What documents do I need to apply for insurance?', a: 'You will need a valid government-issued ID, Social Security number, proof of residence, and information about your current health status. Our team will guide you through the entire process.' },
  { q: 'Can I customize my insurance plan?', a: 'Yes! We offer customizable add-ons for dental, vision, mental health, and prescription coverage. You can tailor your plan to fit your specific healthcare needs.' },
  { q: 'How long does it take for coverage to begin?', a: 'Coverage typically begins within 2-4 weeks after your application is approved. Premium plan members may qualify for accelerated coverage starting as soon as 7 days.' },
  { q: 'Do you accept pre-existing conditions?', a: 'Yes, all our plans cover pre-existing conditions. There is no waiting period for Essential and Premium plans. Family plans have a 90-day waiting period for certain conditions.' },
  { q: 'Can I change my plan after enrollment?', a: 'You can upgrade or downgrade your plan during the annual open enrollment period. Premium and Family members can also make changes during special enrollment periods triggered by life events.' },
  { q: 'Is telemedicine included in all plans?', a: 'Yes, all plans include 24/7 telemedicine access. Essential members get 4 free consultations per year, while Premium and Family members get unlimited telemedicine visits.' },
];

export default function Insurance() {
  const [openFaq, setOpenFaq] = useState(null);

  return (
    <>
      {/* ========== PAGE HEADER ========== */}
      <section className="page-header">
        <div className="container page-header__inner animate-in">
          <span className="section-tag">Insurance</span>
          <h1>Health Insurance Plans</h1>
          <p>
            Flexible and affordable coverage options designed to protect you and your family.
            Compare plans and find the perfect fit for your healthcare needs.
          </p>
        </div>
      </section>

      {/* ========== PLANS ========== */}
      <section className="section insurance-plans">
        <div className="container">
          <div className="plans__grid">
            {plans.map((p, i) => (
              <div
                key={i}
                className={`plan-card animate-in ${p.popular ? 'plan-card--popular' : ''}`}
                style={{ animationDelay: `${0.1 + i * 0.12}s` }}
              >
                {p.popular && <span className="plan-card__badge">Most Popular</span>}
                <h3 className="plan-card__name">{p.name}</h3>
                <div className="plan-card__price">
                  <span className="plan-card__amount">{p.price}</span>
                  <span className="plan-card__period">{p.period}</span>
                </div>
                <p className="plan-card__desc">{p.desc}</p>
                <ul className="plan-card__features">
                  {p.features.map((f, j) => (
                    <li key={j}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0d9488" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                      {f}
                    </li>
                  ))}
                </ul>
                <Link to="/contact" className={`btn ${p.popular ? 'btn-primary' : 'btn-secondary'} plan-card__btn`}>
                  {p.popular ? 'Get Started' : 'Learn More'}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========== COVERAGE HIGHLIGHTS ========== */}
      <section className="section coverage">
        <div className="container">
          <div className="section-header animate-in">
            <span className="section-tag">Coverage</span>
            <h2>What We Cover</h2>
            <p>Our plans provide comprehensive coverage across a wide range of healthcare services.</p>
          </div>
          <div className="coverage__grid">
            {[
              { icon: '🏥', title: 'Hospitalization', desc: 'Inpatient and outpatient hospital care, including surgeries and emergency stays.' },
              { icon: '👨‍⚕️', title: 'Doctor Visits', desc: 'Primary care, specialist consultations, and routine check-ups.' },
              { icon: '💊', title: 'Prescription Drugs', desc: 'Wide formulary coverage for brand-name and generic medications.' },
              { icon: '🧠', title: 'Mental Health', desc: 'Therapy, counseling, and psychiatric care for mental well-being.' },
              { icon: '🤰', title: 'Maternity Care', desc: 'Prenatal, delivery, and postnatal care for new and expecting mothers.' },
              { icon: '🚑', title: 'Emergency Services', desc: 'Ambulance services, ER visits, and urgent care when you need it most.' },
              { icon: '🦷', title: 'Dental & Vision', desc: 'Available as add-on coverage for comprehensive oral and eye care.' },
              { icon: '💻', title: 'Telemedicine', desc: '24/7 virtual consultations with licensed healthcare providers.' },
            ].map((item, i) => (
              <div key={i} className="coverage__card animate-in" style={{ animationDelay: `${0.05 + i * 0.06}s` }}>
                <span className="coverage__icon">{item.icon}</span>
                <h4>{item.title}</h4>
                <p>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========== FAQ ========== */}
      <section className="section faq-section">
        <div className="container">
          <div className="section-header animate-in">
            <span className="section-tag">FAQ</span>
            <h2>Frequently Asked Questions</h2>
            <p>Everything you need to know about our insurance plans and coverage.</p>
          </div>
          <div className="faq__list animate-in">
            {faqs.map((item, i) => (
              <div
                key={i}
                className={`faq__item ${openFaq === i ? 'faq__item--open' : ''}`}
                style={{ animationDelay: `${0.05 + i * 0.06}s` }}
              >
                <button
                  className="faq__question"
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  aria-expanded={openFaq === i}
                >
                  <span>{item.q}</span>
                  <svg
                    width="20" height="20" viewBox="0 0 24 24"
                    fill="none" stroke="currentColor" strokeWidth="2.5"
                    strokeLinecap="round" strokeLinejoin="round"
                    className={`faq__chevron ${openFaq === i ? 'faq__chevron--open' : ''}`}
                  >
                    <polyline points="6 9 12 15 18 9"/>
                  </svg>
                </button>
                <div className="faq__answer">
                  <p>{item.a}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========== CTA ========== */}
      <section className="cta-banner">
        <div className="container">
          <div className="cta-banner__inner animate-in">
            <h2>Need Help Choosing a Plan?</h2>
            <p>Our insurance specialists are here to help you find the perfect coverage.</p>
            <Link to="/contact" className="btn btn-primary">
              Talk to an Advisor
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
