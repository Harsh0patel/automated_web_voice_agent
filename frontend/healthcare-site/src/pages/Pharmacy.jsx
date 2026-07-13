import React, { useState } from 'react';
import './Pharmacy.css';

const categories = [
  { name: 'All', icon: '💊' },
  { name: 'Prescription', icon: '📋' },
  { name: 'Over-the-Counter', icon: '🏪' },
  { name: 'Vitamins & Supplements', icon: '🧪' },
  { name: 'Personal Care', icon: '🧴' },
];

const medications = [
  { name: 'Amoxicillin', category: 'Prescription', desc: 'Antibiotic for bacterial infections', price: '$12.99' },
  { name: 'Lisinopril', category: 'Prescription', desc: 'Blood pressure medication', price: '$8.99' },
  { name: 'Metformin', category: 'Prescription', desc: 'Diabetes management', price: '$6.99' },
  { name: 'Ibuprofen', category: 'Over-the-Counter', desc: 'Pain relief & anti-inflammatory', price: '$9.99' },
  { name: 'Cetirizine', category: 'Over-the-Counter', desc: 'Allergy relief (24hr)', price: '$14.99' },
  { name: 'Vitamin D3', category: 'Vitamins & Supplements', desc: 'Bone health & immunity support', price: '$11.99' },
  { name: 'Omega-3 Fish Oil', category: 'Vitamins & Supplements', desc: 'Heart & brain health', price: '$19.99' },
  { name: 'Hand Sanitizer', category: 'Personal Care', desc: 'Antibacterial gel (8oz)', price: '$5.99' },
  { name: 'Omeprazole', category: 'Over-the-Counter', desc: 'Acid reflux relief', price: '$16.99' },
  { name: 'Atorvastatin', category: 'Prescription', desc: 'Cholesterol management', price: '$10.99' },
  { name: 'Multivitamin', category: 'Vitamins & Supplements', desc: 'Daily essential nutrients', price: '$15.99' },
  { name: 'First Aid Kit', category: 'Personal Care', desc: '30-piece emergency kit', price: '$22.99' },
];

const services = [
  { icon: '💊', title: 'Prescription Refills', desc: 'Request refills online for fast, convenient pickup or delivery.' },
  { icon: '💉', title: 'Vaccinations', desc: 'Get your flu shot, COVID-19, and other recommended vaccines at our pharmacy.' },
  { icon: '🩺', title: 'Health Screenings', desc: 'Free blood pressure checks, glucose testing, and cholesterol screenings.' },
  { icon: '📞', title: 'Medication Counseling', desc: 'Speak with our pharmacists about medication questions and concerns.' },
  { icon: '🏠', title: 'Home Delivery', desc: 'Free home delivery for prescription medications within a 10-mile radius.' },
  { icon: '♻️', title: 'Medication Disposal', desc: 'Safe and environmentally responsible disposal of expired medications.' },
];

export default function Pharmacy() {
  const [activeCategory, setActiveCategory] = useState('All');
  const [refillForm, setRefillForm] = useState({ name: '', rxNumber: '', medication: '' });
  const [refillSent, setRefillSent] = useState(false);

  const filtered = activeCategory === 'All'
    ? medications
    : medications.filter(m => m.category === activeCategory);

  const handleRefillSubmit = (e) => {
    e.preventDefault();
    console.log('Refill request:', refillForm);
    setRefillSent(true);
  };

  return (
    <>
      {/* ========== PAGE HEADER ========== */}
      <section className="page-header">
        <div className="container page-header__inner animate-in">
          <span className="section-tag">Pharmacy</span>
          <h1>Our Pharmacy Services</h1>
          <p>
            Your health and convenience matter to us. Browse our medication catalog,
            request prescription refills, and explore our pharmacy services — all from one place.
          </p>
        </div>
      </section>

      {/* ========== SERVICES ========== */}
      <section className="section pharm-services">
        <div className="container">
          <div className="section-header animate-in">
            <span className="section-tag">Services</span>
            <h2>Pharmacy Services</h2>
            <p>Beyond dispensing medications, we offer a range of services to support your health journey.</p>
          </div>
          <div className="pharm-services__grid">
            {services.map((s, i) => (
              <div key={i} className="pharm-service-card animate-in" style={{ animationDelay: `${0.05 + i * 0.07}s` }}>
                <span className="pharm-service-card__icon">{s.icon}</span>
                <h4>{s.title}</h4>
                <p>{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========== MEDICATIONS CATALOG ========== */}
      <section className="section medications-section">
        <div className="container">
          <div className="section-header animate-in">
            <span className="section-tag">Catalog</span>
            <h2>Medication Catalog</h2>
            <p>Browse our wide selection of prescription and over-the-counter medications.</p>
          </div>

          <div className="meds-filter animate-in">
            {categories.map(cat => (
              <button
                key={cat.name}
                className={`meds-filter__tab ${activeCategory === cat.name ? 'active' : ''}`}
                onClick={() => setActiveCategory(cat.name)}
              >
                {cat.icon} {cat.name}
              </button>
            ))}
          </div>

          <div className="meds__grid">
            {filtered.length > 0 ? (
              filtered.map((med, i) => (
                <div key={i} className="med-card animate-in" style={{ animationDelay: `${0.03 + i * 0.04}s` }}>
                  <div className="med-card__header">
                    <span className="med-card__emoji">💊</span>
                    <span className="med-card__category">{med.category === 'Prescription' ? '📋 Rx' : med.category === 'Over-the-Counter' ? '🏪 OTC' : med.category === 'Vitamins & Supplements' ? '🧪 Vit' : '🧴 Care'}</span>
                  </div>
                  <h3 className="med-card__name">{med.name}</h3>
                  <p className="med-card__desc">{med.desc}</p>
                  <div className="med-card__footer">
                    <span className="med-card__price">{med.price}</span>
                    <button className="btn btn-primary" style={{ padding: '8px 16px', fontSize: '0.8125rem' }}>
                      Add to Cart
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <p className="meds__empty">No medications found in this category.</p>
            )}
          </div>
        </div>
      </section>

      {/* ========== REFILL REQUEST ========== */}
      <section className="section refill-section">
        <div className="container">
          <div className="refill__inner animate-in">
            <div className="refill__info">
              <span className="section-tag">Refill Request</span>
              <h2>Request a Prescription Refill</h2>
              <p>Skip the line! Submit your refill request online and we'll have it ready for pickup within 2 hours.</p>
              <ul className="refill__steps">
                <li>
                  <span className="refill__step-num">1</span>
                  Fill out the form with your details
                </li>
                <li>
                  <span className="refill__step-num">2</span>
                  Our pharmacist verifies your prescription
                </li>
                <li>
                  <span className="refill__step-num">3</span>
                  Get notified when it's ready for pickup
                </li>
              </ul>
            </div>
            <div className="refill__form-wrapper">
              {refillSent ? (
                <div className="refill__success">
                  <span className="refill__success-icon">✅</span>
                  <h3>Refill Request Submitted!</h3>
                  <p>We'll notify you when your prescription is ready. Typically within 2 hours.</p>
                  <button className="btn btn-primary" onClick={() => { setRefillSent(false); setRefillForm({ name: '', rxNumber: '', medication: '' }); }}>
                    Request Another Refill
                  </button>
                </div>
              ) : (
                <form onSubmit={handleRefillSubmit} className="refill__form">
                  <h3>Refill Form</h3>
                  <div className="form__group">
                    <label htmlFor="rx-name">Full Name <span>*</span></label>
                    <input
                      type="text" id="rx-name" name="name"
                      value={refillForm.name}
                      onChange={e => setRefillForm(p => ({ ...p, name: e.target.value }))}
                      placeholder="John Doe" required
                    />
                  </div>
                  <div className="form__group">
                    <label htmlFor="rx-number">Prescription Number <span>*</span></label>
                    <input
                      type="text" id="rx-number" name="rxNumber"
                      value={refillForm.rxNumber}
                      onChange={e => setRefillForm(p => ({ ...p, rxNumber: e.target.value }))}
                      placeholder="RX-XXXX-XXXX" required
                    />
                  </div>
                  <div className="form__group">
                    <label htmlFor="rx-medication">Medication Name</label>
                    <input
                      type="text" id="rx-medication" name="medication"
                      value={refillForm.medication}
                      onChange={e => setRefillForm(p => ({ ...p, medication: e.target.value }))}
                      placeholder="e.g. Amoxicillin"
                    />
                  </div>
                  <button type="submit" className="btn btn-primary form__submit">
                    Submit Refill Request
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M5 12h14M12 5l7 7-7 7"/>
                    </svg>
                  </button>
                </form>
              )}
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
