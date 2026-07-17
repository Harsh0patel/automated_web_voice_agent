import React, { useState, useMemo } from 'react';

/**
 * DynamicPageRenderer — renders components from scraped data generically.
 *
 * Takes a list of component objects (from the DB) and renders them as
 * appropriate UI elements based on their type. This makes the frontend
 * work with ANY site's data, not just MediCare+.
 *
 * Supported component types:
 *   - hero: Large banner with heading and description
 *   - service: Card grid with icon, title, description, features
 *   - doctor: Profile card with name, specialty, experience
 *   - testimonial: Quote card with author, rating
 *   - stat: Number with label
 *   - faq: Accordion with question/answer
 *   - insurance_plan: Pricing card with features
 *   - medication: Product card with price
 *   - blog_post: Article card with meta
 *   - job: Job listing card
 *   - value, why_choose, benefit, coverage_item: Info card
 *   - contact_info: Contact details card
 *   - heading: Section heading
 *   - paragraph: Text paragraph
 *   - list_item: Bullet item
 *   - cta: Call-to-action banner
 *   - milestone: Timeline item
 */

/* =============================================
   Generic Card Components
   ============================================= */

function GenericCard({ component }) {
  const { type, content, metadata = {} } = component;
  const desc = metadata.description || '';
  const attrs = metadata.attributes || {};

  switch (type) {
    case 'hero':
      return <HeroCard content={content} desc={desc} />;

    case 'service':
      return <ServiceCard content={content} desc={desc} attrs={attrs} />;

    case 'doctor':
      return (
        <DoctorCard
          name={content}
          specialty={metadata.specialty || ''}
          experience={metadata.experience || ''}
          desc={desc}
        />
      );

    case 'testimonial':
      return (
        <TestimonialCard
          text={content}
          author={metadata.name || ''}
          role={metadata.role || ''}
          rating={metadata.rating || 0}
        />
      );

    case 'stat':
      return <StatCard value={metadata.value || content} label={metadata.label || ''} />;

    case 'faq':
      return <FaqCard question={content} answer={metadata.answer || ''} />;

    case 'insurance_plan':
      return (
        <PlanCard
          name={content}
          price={metadata.price || ''}
          desc={desc}
          features={metadata.features || []}
          popular={metadata.popular || false}
        />
      );

    case 'medication':
      return (
        <MedicationCard
          name={content}
          desc={desc}
          price={metadata.price || ''}
          category={metadata.category || ''}
        />
      );

    case 'blog_post':
      return (
        <BlogCard
          title={content}
          excerpt={metadata.excerpt || ''}
          author={metadata.author || ''}
          category={metadata.category || ''}
          meta={metadata.meta || ''}
        />
      );

    case 'job':
      return (
        <JobCard
          title={content}
          desc={desc}
          tags={metadata.tags || []}
        />
      );

    case 'contact_info':
      return <ContactInfoCard content={content} metadata={metadata} />;

    case 'cta':
      return <CtaCard content={content} desc={desc} />;

    case 'milestone':
      return <MilestoneItem content={content} metadata={metadata} />;

    case 'value':
    case 'why_choose':
    case 'benefit':
    case 'coverage_item':
      return <InfoCard icon={attrs.icon || ''} title={content} desc={desc} />;

    case 'heading':
      return <SectionHeading content={content} level={metadata.level || 'h2'} />;

    case 'paragraph':
      return <p className="dp-paragraph">{content}</p>;

    case 'list_item':
      return <li className="dp-list-item">{content}</li>;

    default:
      return (
        <div className="dp-generic-card">
          <h4>{content}</h4>
          {desc && <p>{desc}</p>}
        </div>
      );
  }
}

/* =============================================
   Individual Card Components
   ============================================= */

function HeroCard({ content, desc }) {
  return (
    <div className="dp-hero">
      <div className="container dp-hero__inner">
        <h1 className="dp-hero__title">{content}</h1>
        {desc && <p className="dp-hero__desc">{desc}</p>}
      </div>
    </div>
  );
}

function ServiceCard({ content, desc, attrs }) {
  const features = attrs.features || [];
  return (
    <div className="dp-card dp-service-card">
      {attrs.icon && <div className="dp-card__icon">{attrs.icon}</div>}
      <h3 className="dp-card__title">{content}</h3>
      {desc && <p className="dp-card__desc">{desc}</p>}
      {features.length > 0 && (
        <ul className="dp-card__features">
          {features.map((f, i) => (
            <li key={i}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              {f}
            </li>
          ))}
        </ul>
      )}
      {attrs.link && (
        <a href={attrs.link} className="dp-card__link">
          Learn more →
        </a>
      )}
    </div>
  );
}

function DoctorCard({ name, specialty, experience, desc }) {
  const initials = name.split(' ').map(n => n[0]).join('').slice(0, 2);
  const colors = ['#0d9488', '#0891b2', '#7c3aed', '#ea580c', '#dc2626', '#ca8a04'];
  const color = colors[name.length % colors.length];

  return (
    <div className="dp-card dp-doctor-card">
      <div className="dp-doctor-card__avatar" style={{ background: color }}>{initials}</div>
      <h3 className="dp-card__title">{name}</h3>
      {specialty && <span className="dp-doctor-card__specialty">{specialty}</span>}
      {experience && <span className="dp-doctor-card__exp">{experience}</span>}
      {desc && <p className="dp-card__desc">{desc}</p>}
    </div>
  );
}

function TestimonialCard({ text, author, role, rating }) {
  return (
    <div className="dp-card dp-testimonial-card">
      <div className="dp-testimonial-card__stars">
        {'★'.repeat(rating)}{'☆'.repeat(Math.max(0, 5 - rating))}
      </div>
      <p className="dp-testimonial-card__text">"{text}"</p>
      {(author || role) && (
        <div className="dp-testimonial-card__author">
          <strong>{author}</strong>
          {role && <small>{role}</small>}
        </div>
      )}
    </div>
  );
}

function StatCard({ value, label }) {
  return (
    <div className="dp-stat-card">
      <span className="dp-stat-card__value">{value}</span>
      {label && <span className="dp-stat-card__label">{label}</span>}
    </div>
  );
}

function FaqCard({ question, answer }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`dp-faq-card ${open ? 'dp-faq-card--open' : ''}`}>
      <button className="dp-faq-card__question" onClick={() => setOpen(!open)} aria-expanded={open}>
        <span>{question}</span>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
          className={`dp-faq-card__chevron ${open ? 'dp-faq-card__chevron--open' : ''}`}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>
      {open && answer && (
        <div className="dp-faq-card__answer">
          <p>{answer}</p>
        </div>
      )}
    </div>
  );
}

function PlanCard({ name, price, desc, features, popular }) {
  return (
    <div className={`dp-card dp-plan-card ${popular ? 'dp-plan-card--popular' : ''}`}>
      {popular && <span className="dp-plan-card__badge">Most Popular</span>}
      <h3 className="dp-card__title">{name}</h3>
      {price && <div className="dp-plan-card__price">{price}</div>}
      {desc && <p className="dp-card__desc">{desc}</p>}
      {features.length > 0 && (
        <ul className="dp-plan-card__features">
          {features.map((f, i) => (
            <li key={i}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              {f}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function MedicationCard({ name, desc, price, category }) {
  return (
    <div className="dp-card dp-med-card">
      <h3 className="dp-card__title">{name}</h3>
      {category && <span className="dp-med-card__category">{category}</span>}
      {desc && <p className="dp-card__desc">{desc}</p>}
      {price && <div className="dp-med-card__footer"><span className="dp-med-card__price">{price}</span></div>}
    </div>
  );
}

function BlogCard({ title, excerpt, author, category, meta }) {
  return (
    <div className="dp-card dp-blog-card">
      {category && <span className="dp-blog-card__category">{category}</span>}
      <h3 className="dp-card__title">{title}</h3>
      {excerpt && <p className="dp-card__desc">{excerpt}</p>}
      {(author || meta) && (
        <div className="dp-blog-card__footer">
          {author && <span className="dp-blog-card__author">{author}</span>}
          {meta && <span className="dp-blog-card__meta">{meta}</span>}
        </div>
      )}
    </div>
  );
}

function JobCard({ title, desc, tags }) {
  return (
    <div className="dp-card dp-job-card">
      <h3 className="dp-card__title">{title}</h3>
      {desc && <p className="dp-card__desc">{desc}</p>}
      {tags.length > 0 && (
        <div className="dp-job-card__tags">
          {tags.map((tag, i) => (
            <span key={i} className="dp-job-card__tag">{tag}</span>
          ))}
        </div>
      )}
    </div>
  );
}

function ContactInfoCard({ content, metadata }) {
  return (
    <div className="dp-card dp-contact-card">
      <h4>{content}</h4>
      {metadata.address && <p>{metadata.address}</p>}
      {metadata.phone && <p>{metadata.phone}</p>}
      {metadata.email && <p>{metadata.email}</p>}
      {metadata.hours && <p>{metadata.hours}</p>}
    </div>
  );
}

function CtaCard({ content, desc }) {
  return (
    <div className="dp-cta">
      <div className="container dp-cta__inner">
        <h2>{content}</h2>
        {desc && <p>{desc}</p>}
      </div>
    </div>
  );
}

function MilestoneItem({ content, metadata }) {
  return (
    <div className="dp-milestone">
      <div className="dp-milestone__dot" />
      <div className="dp-milestone__content">
        {metadata.year && <span className="dp-milestone__year">{metadata.year}</span>}
        <h4>{content}</h4>
        {metadata.description && <p>{metadata.description}</p>}
      </div>
    </div>
  );
}

function InfoCard({ icon, title, desc }) {
  return (
    <div className="dp-card dp-info-card">
      {icon && <div className="dp-card__icon">{icon}</div>}
      <h4 className="dp-card__title">{title}</h4>
      {desc && <p className="dp-card__desc">{desc}</p>}
    </div>
  );
}

function SectionHeading({ content, level }) {
  const Tag = level || 'h2';
  return <Tag className="dp-section-heading">{content}</Tag>;
}

/* =============================================
   Main Component
   ============================================= */

export default function DynamicPageRenderer({ components = [], title = '', subtitle = '' }) {
  // Group components by type for layout
  const grouped = useMemo(() => {
    const groups = {};
    const layoutOrder = [
      'hero', 'cta', 'stat', 'service', 'doctor', 'testimonial', 'faq',
      'insurance_plan', 'medication', 'blog_post', 'job', 'milestone',
      'value', 'why_choose', 'benefit', 'coverage_item', 'contact_info',
      'heading', 'paragraph', 'list_item',
    ];

    for (const comp of components) {
      const type = comp.type || 'unknown';
      if (!groups[type]) groups[type] = [];
      groups[type].push(comp);
    }

    // Sort groups by layout order
    const sorted = [];
    const seen = new Set();
    for (const type of layoutOrder) {
      if (groups[type] && !seen.has(type)) {
        sorted.push({ type, items: groups[type] });
        seen.add(type);
      }
    }
    for (const type of Object.keys(groups)) {
      if (!seen.has(type)) {
        sorted.push({ type, items: groups[type] });
        seen.add(type);
      }
    }

    return sorted;
  }, [components]);

  if (!components || components.length === 0) {
    return (
      <div className="dp-empty">
        <div className="container">
          <h2>{title || 'Page Content'}</h2>
          {subtitle && <p>{subtitle}</p>}
          <p className="dp-empty__text">No components available yet. Try scraping the site first!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dp-page">
      {/* Page header if title provided */}
      {title && (
        <div className="dp-page-header">
          <div className="container dp-page-header__inner">
            <h1>{title}</h1>
            {subtitle && <p>{subtitle}</p>}
          </div>
        </div>
      )}

      {/* Render each group */}
      {grouped.map(({ type, items }) => (
        <DynamicSection key={type} type={type} items={items} />
      ))}
    </div>
  );
}

/**
 * DynamicSection renders a group of components of the same type
 * with appropriate layout (grid, list, single).
 */
function DynamicSection({ type, items }) {
  const label = type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

  // Determine layout based on type
  const layouts = {
    hero: 'single',
    cta: 'single',
    heading: 'single',
    paragraph: 'single',
    stat: 'grid-4',
    service: 'grid-3',
    doctor: 'grid-3',
    testimonial: 'grid-3',
    insurance_plan: 'grid-3',
    medication: 'grid-3',
    blog_post: 'grid-3',
    job: 'list',
    milestone: 'list',
    faq: 'list',
    value: 'grid-3',
    why_choose: 'grid-3',
    benefit: 'grid-4',
    coverage_item: 'grid-4',
    contact_info: 'grid-2',
    list_item: 'list',
  };

  const layout = layouts[type] || 'grid-3';

  return (
    <section className={`dp-section dp-section--${type}`}>
      <div className="container">
        {/* Section heading (skip for standalone hero/heading) */}
        {type !== 'hero' && type !== 'heading' && items.length > 1 && (
          <div className="dp-section-header">
            <h2>{label}</h2>
          </div>
        )}

        {layout === 'single' ? (
          // Single item layout (hero, cta)
          items.map((item, i) => <GenericCard key={i} component={item} />)
        ) : layout === 'list' ? (
          // Vertical list layout (jobs, faqs, milestones)
          <div className="dp-list">
            {items.map((item, i) => (
              <div key={i} className="dp-list__item" style={{ animationDelay: `${i * 0.05}s` }}>
                <GenericCard component={item} />
              </div>
            ))}
          </div>
        ) : layout === 'grid-4' ? (
          // 4-column grid (stats, benefits)
          <div className="dp-grid dp-grid--4">
            {items.map((item, i) => (
              <div key={i} className="dp-grid__item" style={{ animationDelay: `${i * 0.06}s` }}>
                <GenericCard component={item} />
              </div>
            ))}
          </div>
        ) : layout === 'grid-2' ? (
          // 2-column grid (contact info)
          <div className="dp-grid dp-grid--2">
            {items.map((item, i) => (
              <div key={i} className="dp-grid__item" style={{ animationDelay: `${i * 0.06}s` }}>
                <GenericCard component={item} />
              </div>
            ))}
          </div>
        ) : (
          // Default: 3-column grid (services, doctors, testimonials, etc.)
          <div className="dp-grid dp-grid--3">
            {items.map((item, i) => (
              <div key={i} className="dp-grid__item" style={{ animationDelay: `${i * 0.06}s` }}>
                <GenericCard component={item} />
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
