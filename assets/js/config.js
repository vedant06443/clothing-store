/**
 * Suyog Textile — Central Business & Supabase Configuration
 * Single Source of Truth across all static storefront pages.
 */
window.SITE_CONFIG = {
  brandName: "Suyog Textile",
  tagline: "Traditional Indian Wear",
  
  // Supabase Client Settings (PUBLIC anon key and URL; security enforced via RLS)
  supabaseUrl: "https://woaubpvkzvxbksntreki.supabase.co",
  supabaseAnonKey: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndvYXVicHZrenZ4YmtzbnRyZWtpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTI5MDI5NjcsImV4cCI6MjEwODQ3ODk2N30.so7cDcU3bzfAWDa0gTDeMcGRDkbHitrfS2N25IFZVpI",

  // Online Payment Flag (Kept false until Phase 5 is explicitly ordered)
  onlinePaymentEnabled: false,

  // Shipping Rules
  freeShippingThreshold: 1499,
  shippingFee: 0, // TODO_CONFIRM: Seeded as 0 for orders below ₹1,499. Update when confirmed.
  
  // Standard Coupons
  coupons: [
    {
      code: "WELCOME10",
      discountType: "percent",
      discountValue: 10,
      minOrder: 999,
      description: "10% off on handloom sarees and readymade kurtis",
      eligibleCategories: ["sarees", "kurtis"]
    },
    {
      code: "FESTIVE20",
      discountType: "percent",
      discountValue: 20,
      minOrder: 2999,
      description: "20% off on bridal lehengas and wedding ensembles",
      eligibleCategories: ["lehengas", "salwar-suits", "dresses"]
    },
    {
      code: "FLAT500",
      discountType: "flat",
      discountValue: 500,
      minOrder: 3999,
      description: "Flat ₹500 off on Kanjivaram and Banarasi silk sarees",
      eligibleCategories: ["sarees"]
    }
  ],

  // Store Hours & Contact Details
  storeHours: "10:00 AM – 8:30 PM, all days",
  address: "Lahoti Mala, 484, Jadhav Sankul road, Ashoknagar, Satpur Colony, Nashik, Maharashtra 422007",
  mapsUrl: "https://maps.google.com/?q=Lahoti+Mala,+484,+Jadhav+Sankul+road,+Ashoknagar,+Satpur+Colony,+Nashik,+Maharashtra+422007",
  
  phones: [
    { display: "0253 4515460", tel: "02534515460" },
    { display: "+91 86693 96037", tel: "+918669396037" }
  ],
  whatsappNumber: "918669396037",
  whatsappUrl: "https://wa.me/918669396037",

  email: "TODO_CONFIRM", // TODO_CONFIRM: Official business email address

  socialUrls: {
    whatsapp: "https://wa.me/918669396037",
    instagram: "TODO_CONFIRM", // TODO_CONFIRM: Official Instagram profile URL
    facebook: "TODO_CONFIRM",  // TODO_CONFIRM: Official Facebook page URL
    youtube: "TODO_CONFIRM"    // TODO_CONFIRM: Official YouTube channel URL
  },

  paymentLinkUrl: "TODO_CONFIRM", // TODO_CONFIRM: External payment link if any

  legal: {
    legalName: "TODO_CONFIRM",        // TODO_CONFIRM: Registered legal entity name
    gstin: "TODO_CONFIRM",            // TODO_CONFIRM: 15-digit GSTIN
    grievanceOfficer: "TODO_CONFIRM", // TODO_CONFIRM: Grievance Officer name
    grievanceContact: "TODO_CONFIRM", // TODO_CONFIRM: Grievance Officer contact info
    refundPolicy: "TODO_CONFIRM"      // TODO_CONFIRM: Confirmation of refund vs exchange policy
  }
};
