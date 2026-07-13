import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import BookingStepIndicator from './BookingStepIndicator.jsx';
import { ArrowRight, ArrowLeft, ChevronLeft, ChevronRight } from '../utils/icons.jsx';
import './Booking.css';

/* =============================================
   Seed data
   ============================================= */
const services = [
  { id: 'cardiology', name: 'Cardiology', icon: '❤️' },
  { id: 'neurology', name: 'Neurology', icon: '🧠' },
  { id: 'pediatrics', name: 'Pediatrics', icon: '👶' },
  { id: 'orthopedics', name: 'Orthopedics', icon: '🦴' },
  { id: 'pulmonology', name: 'Pulmonology', icon: '🫁' },
  { id: 'oncology', name: 'Oncology', icon: '🧬' },
  { id: 'ophthalmology', name: 'Ophthalmology', icon: '👁️' },
  { id: 'general', name: 'General Checkup', icon: '🩺' },
];

const doctors = [
  { id: 1, name: 'Dr. Sarah Mitchell', specialty: 'cardiology', initials: 'SM', color: '#0d9488' },
  { id: 2, name: 'Dr. James Wilson', specialty: 'neurology', initials: 'JW', color: '#0891b2' },
  { id: 3, name: 'Dr. Emily Park', specialty: 'pediatrics', initials: 'EP', color: '#7c3aed' },
  { id: 4, name: 'Dr. Robert Chen', specialty: 'orthopedics', initials: 'RC', color: '#ea580c' },
  { id: 5, name: 'Dr. Lisa Thompson', specialty: 'oncology', initials: 'LT', color: '#dc2626' },
  { id: 6, name: 'Dr. Michael Rivera', specialty: 'pulmonology', initials: 'MR', color: '#ca8a04' },
  { id: 7, name: 'Dr. Anna Kowalski', specialty: 'ophthalmology', initials: 'AK', color: '#0891b2' },
  { id: 8, name: 'Dr. David Okafor', specialty: 'general', initials: 'DO', color: '#0d9488' },
];

const TIME_SLOTS = [
  '8:00 AM', '8:30 AM', '9:00 AM', '9:30 AM', '10:00 AM', '10:30 AM',
  '11:00 AM', '11:30 AM', '1:00 PM', '1:30 PM', '2:00 PM', '2:30 PM',
  '3:00 PM', '3:30 PM', '4:00 PM', '4:30 PM',
];

// Shorter month/day names to reduce bundle size
const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const DAYS_SHORT = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];

const mockBooked = (dateStr) => {
  const day = new Date(dateStr).getDate();
  const booked = [];
  if (day % 2 === 0) booked.push('9:00 AM', '10:30 AM', '2:00 PM');
  if (day % 3 === 0) booked.push('11:00 AM', '3:30 PM');
  if (day > 20) booked.push('8:00 AM', '8:30 AM');
  return booked;
};

/* =============================================
   Calendar helper
   ============================================= */
function getCalendarDays(year, month) {
  const first = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const days = [];
  for (let i = 0; i < first; i++) days.push(null);
  for (let d = 1; d <= daysInMonth; d++) days.push(d);
  return days;
}

/* =============================================
   Component
   ============================================= */
export default function Booking() {
  const [step, setStep] = useState(1);
  const today = new Date();

  const [selectedService, setSelectedService] = useState('');
  const [selectedDoctor, setSelectedDoctor] = useState(null);
  const [calYear, setCalYear] = useState(today.getFullYear());
  const [calMonth, setCalMonth] = useState(today.getMonth());
  const [selectedDate, setSelectedDate] = useState(null);
  const [selectedTime, setSelectedTime] = useState('');
  const [patient, setPatient] = useState({ name: '', email: '', phone: '', notes: '' });
  const [confirmed, setConfirmed] = useState(false);

  const calendarDays = useMemo(() => getCalendarDays(calYear, calMonth), [calYear, calMonth]);
  const filteredDoctors = useMemo(
    () => doctors.filter(d => d.specialty === selectedService),
    [selectedService]
  );

  const selectedDateStr = selectedDate
    ? `${calYear}-${String(calMonth + 1).padStart(2, '0')}-${String(selectedDate).padStart(2, '0')}`
    : null;
  const bookedSlots = selectedDateStr ? mockBooked(selectedDateStr) : [];

  const isPastDate = (day) => {
    const d = new Date(calYear, calMonth, day);
    const t = new Date();
    t.setHours(0, 0, 0, 0);
    return d < t;
  };

  const goNext = () => setStep(s => Math.min(s + 1, 5));
  const goBack = () => setStep(s => Math.max(s - 1, 1));

  const handleConfirm = (e) => {
    e.preventDefault();
    setConfirmed(true);
  };

  const serviceName = services.find(s => s.id === selectedService)?.name || '';
  const doctorName = selectedDoctor
    ? doctors.find(d => d.id === selectedDoctor)?.name || ''
    : '';
  const selectedServiceObj = services.find(s => s.id === selectedService);

  const fullDate = selectedDate ? `${MONTHS[calMonth]} ${selectedDate}, ${calYear}` : '';

  // ========== RENDER STEPS ==========

  const renderServiceStep = () => (
    <div className="booking__step-content animate-in">
      <h2>Select a Service</h2>
      <p>Choose the type of appointment you'd like to book.</p>
      <div className="booking__service-grid">
        {services.map(s => (
          <button
            key={s.id}
            className={`booking__service-card ${selectedService === s.id ? 'booking__service-card--selected' : ''}`}
            onClick={() => setSelectedService(s.id)}
          >
            <span className="booking__service-icon">{s.icon}</span>
            <span className="booking__service-name">{s.name}</span>
          </button>
        ))}
      </div>
    </div>
  );

  const renderDoctorStep = () => (
    <div className="booking__step-content animate-in">
      <h2>Select a Doctor</h2>
      <p>Our specialists for <strong>{serviceName}</strong>.</p>
      <div className="booking__doctor-grid">
        {filteredDoctors.map(d => (
          <button
            key={d.id}
            className={`booking__doctor-card ${selectedDoctor === d.id ? 'booking__doctor-card--selected' : ''}`}
            onClick={() => setSelectedDoctor(d.id)}
          >
            <div className="booking__doctor-avatar" style={{ background: d.color }}>{d.initials}</div>
            <div>
              <strong>{d.name}</strong>
              <small>{serviceName}</small>
            </div>
          </button>
        ))}
      </div>
    </div>
  );

  const renderDateTimeStep = () => {
    const prevMonth = () => {
      if (calMonth === 0) { setCalYear(y => y - 1); setCalMonth(11); }
      else setCalMonth(m => m - 1);
    };
    const nextMonth = () => {
      if (calMonth === 11) { setCalYear(y => y + 1); setCalMonth(0); }
      else setCalMonth(m => m + 1);
    };

    return (
      <div className="booking__step-content animate-in">
        <h2>Select Date & Time</h2>
        <p>Pick an available day and time slot.</p>
        <div className="booking__datetime-grid">
          <div className="booking__calendar">
            <div className="booking__cal-header">
              <button onClick={prevMonth} className="booking__cal-nav" aria-label="Previous month">
                <ChevronLeft />
              </button>
              <span className="booking__cal-month">{MONTHS[calMonth]} {calYear}</span>
              <button onClick={nextMonth} className="booking__cal-nav" aria-label="Next month">
                <ChevronRight />
              </button>
            </div>
            <div className="booking__cal-days-header">
              {DAYS_SHORT.map(d => <span key={d}>{d}</span>)}
            </div>
            <div className="booking__cal-grid">
              {calendarDays.map((day, i) => (
                <button
                  key={i}
                  className={`booking__cal-day ${!day ? 'booking__cal-day--empty' : ''} ${day && selectedDate === day ? 'booking__cal-day--selected' : ''} ${day && isPastDate(day) ? 'booking__cal-day--past' : ''}`}
                  disabled={!day || isPastDate(day)}
                  onClick={() => { setSelectedDate(day); setSelectedTime(''); }}
                >
                  {day || ''}
                </button>
              ))}
            </div>
          </div>
          <div className="booking__timeslots">
            <h4 className="booking__timeslots-title">
              {selectedDate ? fullDate : 'Select a date'}
            </h4>
            {selectedDate ? (
              <div className="booking__timeslots-grid">
                {TIME_SLOTS.map(slot => {
                  const booked = bookedSlots.includes(slot);
                  return (
                    <button
                      key={slot}
                      className={`booking__timeslot ${selectedTime === slot ? 'booking__timeslot--selected' : ''} ${booked ? 'booking__timeslot--booked' : ''}`}
                      disabled={booked}
                      onClick={() => setSelectedTime(slot)}
                    >
                      {booked ? '❌' : '✓'} {slot}
                    </button>
                  );
                })}
              </div>
            ) : (
              <p className="booking__timeslots-hint">Please select a date to see available times.</p>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderPatientInfoStep = () => (
    <div className="booking__step-content animate-in">
      <h2>Your Information</h2>
      <p>Please provide your contact details so we can confirm your appointment.</p>
      <div className="booking__summary">
        <div className="booking__summary-row">
          <span>Service</span>
          <strong>{selectedServiceObj?.icon} {serviceName}</strong>
        </div>
        <div className="booking__summary-row">
          <span>Doctor</span>
          <strong>{doctorName}</strong>
        </div>
        <div className="booking__summary-row">
          <span>Date & Time</span>
          <strong>{fullDate} at {selectedTime}</strong>
        </div>
      </div>
      <form onSubmit={handleConfirm} className="booking__form" id="booking-form">
        <div className="form__row">
          <div className="form__group">
            <label htmlFor="b-name">Full Name <span>*</span></label>
            <input type="text" id="b-name" value={patient.name} onChange={e => setPatient(p => ({ ...p, name: e.target.value }))} placeholder="John Doe" required />
          </div>
          <div className="form__group">
            <label htmlFor="b-email">Email <span>*</span></label>
            <input type="email" id="b-email" value={patient.email} onChange={e => setPatient(p => ({ ...p, email: e.target.value }))} placeholder="john@example.com" required />
          </div>
        </div>
        <div className="form__row">
          <div className="form__group">
            <label htmlFor="b-phone">Phone <span>*</span></label>
            <input type="tel" id="b-phone" value={patient.phone} onChange={e => setPatient(p => ({ ...p, phone: e.target.value }))} placeholder="+1 (555) 123-4567" required />
          </div>
          <div className="form__group">
            <label htmlFor="b-notes">Notes (optional)</label>
            <input type="text" id="b-notes" value={patient.notes} onChange={e => setPatient(p => ({ ...p, notes: e.target.value }))} placeholder="Any special requests?" />
          </div>
        </div>
        <button type="submit" className="btn btn-primary form__submit">
          Confirm Appointment
          <ArrowRight />
        </button>
      </form>
    </div>
  );

  const renderConfirmation = () => (
    <div className="booking__step-content booking__confirmed animate-in">
      <div className="booking__confirmed-icon">✅</div>
      <h2>Appointment Confirmed! 🎉</h2>
      <p>A confirmation email will be sent to <strong>{patient.email}</strong>.</p>
      <div className="booking__confirmed-card">
        <div className="booking__confirmed-row"><span>📋 Service</span><strong>{selectedServiceObj?.icon} {serviceName}</strong></div>
        <div className="booking__confirmed-row"><span>👨‍⚕️ Doctor</span><strong>{doctorName}</strong></div>
        <div className="booking__confirmed-row"><span>📅 Date</span><strong>{fullDate}</strong></div>
        <div className="booking__confirmed-row"><span>⏰ Time</span><strong>{selectedTime}</strong></div>
        <div className="booking__confirmed-row"><span>👤 Patient</span><strong>{patient.name}</strong></div>
      </div>
      <div className="booking__confirmed-actions">
        <Link to="/" className="btn btn-primary">Back to Home</Link>
        <button className="btn btn-secondary" onClick={() => {
          setStep(1); setSelectedService(''); setSelectedDoctor(null);
          setSelectedDate(null); setSelectedTime('');
          setPatient({ name: '', email: '', phone: '', notes: '' });
          setConfirmed(false);
        }}>
          Book Another
        </button>
      </div>
    </div>
  );

  const renderStepContent = () => {
    if (confirmed) return renderConfirmation();
    switch (step) {
      case 1: return renderServiceStep();
      case 2: return renderDoctorStep();
      case 3: return renderDateTimeStep();
      case 4: return renderPatientInfoStep();
      default: return null;
    }
  };

  const canGoNext = () => {
    switch (step) {
      case 1: return !!selectedService;
      case 2: return !!selectedDoctor;
      case 3: return !!(selectedDate && selectedTime);
      case 4: return patient.name && patient.email && patient.phone;
      default: return false;
    }
  };

  return (
    <>
      <section className="page-header">
        <div className="container page-header__inner animate-in">
          <span className="section-tag">Booking</span>
          <h1>Book an Appointment</h1>
          <p>Schedule your visit with our medical specialists in just a few easy steps.</p>
        </div>
      </section>
      <section className="section booking-section">
        <div className="container">
          {!confirmed && <BookingStepIndicator currentStep={step} />}
          {renderStepContent()}
          {!confirmed && (
            <div className="booking__nav">
              {step > 1 && (
                <button className="btn btn-secondary" onClick={goBack}>
                  <ArrowLeft /> Back
                </button>
              )}
              {step < 4 ? (
                <button className="btn btn-primary" onClick={goNext} disabled={!canGoNext()}>
                  Next Step <ArrowRight />
                </button>
              ) : step === 4 ? (
                <button className="btn btn-primary" onClick={handleConfirm} disabled={!canGoNext()} form="booking-form">
                  Confirm Appointment <ArrowRight />
                </button>
              ) : null}
            </div>
          )}
        </div>
      </section>
    </>
  );
}
