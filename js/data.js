// Realistic Mock Data for UdyamSetu Platform

const UDYAM_DATA = {
  currentUser: {
    name: "Ananya Sharma",
    initials: "AS",
    category: "Agri-Tech & Handlooms",
    location: "Jaipur, Rajasthan",
    avatar: "assets/images/digital_rahul.jpg"
  },

  entrepreneurs: [
    {
      id: "asha-devi",
      name: "Asha Devi",
      verified: true,
      category: "Handicrafts",
      location: "Uttar Pradesh",
      avatar: "assets/images/artisan_asha.jpg",
      quote: "Preserving traditional craftsmanship while creating new opportunities for rural artisans.",
      description: "Handmade bags, home decor and traditional crafts. Looking for marketing and distribution partners.",
      fullStory: "We create handmade bags, home decor and traditional crafts using local natural materials like moonj grass, cane, and clay. Our enterprise empowers over 45 rural women with sustainable dignified livelihoods, taking local indigenous craft to national and export exhibitions.",
      lookingFor: ["Marketing partners", "Distributors", "E-commerce support"],
      products: [
        { name: "Handwoven Moonj Baskets", price: "₹450 - ₹1,200", image: "assets/images/hero_entrepreneur.jpg" },
        { name: "Terracotta Painted Vessels", price: "₹350 - ₹800", image: "assets/images/potter_artisan.jpg" },
        { name: "Traditional Block-Printed Bags", price: "₹500 - ₹1,500", image: "assets/images/village_journey.jpg" }
      ]
    },
    {
      id: "green-harvest",
      name: "Green Harvest",
      verified: true,
      category: "Agriculture",
      location: "Madhya Pradesh",
      avatar: "assets/images/farmer_greenharvest.jpg",
      quote: "Pioneering organic soil regeneration and community crop aggregation.",
      description: "Organic pulses, spices and farm products. Open to collaborations for packaging and wider distribution.",
      fullStory: "A collective of 120 smallholder organic farmers in central Madhya Pradesh specializing in chemical-free black wheat, cold-pressed mustard oil, organic chickpea, and natural turmeric.",
      lookingFor: ["Packaging partners", "Bulk buyers", "Logistics support"],
      products: [
        { name: "Organic Desi Chana (1kg)", price: "₹120", image: "assets/images/farmer_greenharvest.jpg" },
        { name: "Cold-Pressed Mustard Oil (1L)", price: "₹220", image: "assets/images/packaging_spices.jpg" },
        { name: "Natural High-Curcumin Turmeric", price: "₹180", image: "assets/images/packaging_spices.jpg" }
      ]
    },
    {
      id: "rahul-sharma",
      name: "Rahul Sharma",
      verified: true,
      category: "Digital Services",
      location: "Rajasthan",
      avatar: "assets/images/digital_rahul.jpg",
      quote: "Empowering rural micro-enterprises with practical digital skills and clean branding.",
      description: "Website development, product photography and digital marketing for small businesses.",
      fullStory: "Providing localized digital branding, catalog photography, social media assistance, and WhatsApp store setup for rural self-help groups and grassroots entrepreneurs across western India.",
      lookingFor: ["Artisan clusters", "Agri-FPOs", "Rural cooperatives"],
      products: [
        { name: "Product Shoot & Mobile Catalog", price: "₹3,000", image: "assets/images/phone_photography.jpg" },
        { name: "WhatsApp Business Store Setup", price: "₹2,500", image: "assets/images/digital_rahul.jpg" }
      ]
    },
    {
      id: "meera-patil",
      name: "Meera Patil",
      verified: true,
      category: "Homemade Food Products",
      location: "Maharashtra",
      avatar: "assets/images/meera_patil.jpg",
      quote: "Bringing grandmother's authentic recipes to urban tables with purity.",
      description: "Traditional Maharashtrian dry snacks, cold-stone pounded masalas, and healthy millet cookies.",
      fullStory: "Founded in Satara district, we prepare small-batch stone-ground spices, spicy roasted poha chivda, and multigrain laddus made from organic jaggery.",
      lookingFor: ["Eco-friendly packaging", "Urban retailers", "Courier partners"],
      products: [
        { name: "Kolhapuri Special Kanda Masala", price: "₹190", image: "assets/images/meera_patil.jpg" },
        { name: "Millet & Jaggery Snack Bites", price: "₹160", image: "assets/images/packaging_spices.jpg" }
      ]
    },
    {
      id: "suresh-yadav",
      name: "Suresh Yadav",
      verified: false,
      category: "Organic Products",
      location: "Bihar",
      avatar: "assets/images/suresh_yadav.jpg",
      quote: "Sweetening lives through sustainable wild forest and mustard honey beekeeping.",
      description: "Raw unpasteurized honey, organic beekeeping kits, and seasonal herbal extracts.",
      fullStory: "We run a network of 400 beehives across Muzaffarpur and Samastipur, producing seasonal litchi honey and raw mustard flora honey without artificial additives.",
      lookingFor: ["Distributors", "Eco-packaging jars", "Interstate transport"],
      products: [
        { name: "Pure Raw Litchi Honey (500g)", price: "₹340", image: "assets/images/suresh_yadav.jpg" }
      ]
    },
    {
      id: "ramesh-kumar",
      name: "Ramesh Kumar",
      verified: true,
      category: "Agriculture",
      location: "Karnataka",
      avatar: "assets/images/ramesh_kumar.jpg",
      quote: "Bridging the gap between south Indian spice growers and national buyers.",
      description: "Organic turmeric, cardamom, and black pepper grown in the Western Ghats foothills.",
      fullStory: "Family farming legacy now modernized into an organic farmer producer cluster cultivating high-grade GI turmeric and aromatic spices.",
      lookingFor: ["Interstate buyers", "Wholesale partners", "FSSAI compliance guidance"],
      products: [
        { name: "Western Ghats Black Pepper", price: "₹450 / 500g", image: "assets/images/packaging_spices.jpg" }
      ]
    }
  ],

  collaborations: [
    {
      id: "collab-1",
      title: "Looking for Packaging Partner",
      subtitle: "Need eco-friendly packaging solutions for our food products.",
      category: "Food Products",
      type: "Seeking Partners",
      tag: "Packaging",
      location: "Maharashtra",
      authorName: "Meera Patil",
      authorAvatar: "assets/images/meera_patil.jpg",
      timeAgo: "2 days ago",
      thumb: "assets/images/packaging_spices.jpg",
      fullDescription: "We currently manufacture over 500 kg of traditional dried snacks and roasted millet items monthly in Satara, Maharashtra. We are looking for a reliable supplier or collaborator who can provide biodegradable, moisture-resistant pouch packaging with custom printed labels that keep shelf life intact."
    },
    {
      id: "collab-2",
      title: "Marketing Collaboration",
      subtitle: "Looking for a digital marketing partner to help showcase our handicraft products online.",
      category: "Handicrafts",
      type: "Seeking Partners",
      tag: "Marketing",
      location: "Uttar Pradesh",
      authorName: "Asha Devi",
      authorAvatar: "assets/images/artisan_asha.jpg",
      timeAgo: "3 days ago",
      thumb: "assets/images/crafts_banner.jpg",
      fullDescription: "Our women's artisan collective creates premium quality moonj and terracotta home decor. We seek a digital marketing and social media collaborator who can run focused online promotions and assist us with Amazon Karigar / ONDC cataloging."
    },
    {
      id: "collab-3",
      title: "Joint Product Development",
      subtitle: "Looking for someone to collaborate on a new range of organic spice blends.",
      category: "Agriculture",
      type: "Seeking Partners",
      tag: "Product Development",
      location: "Madhya Pradesh",
      authorName: "Green Harvest",
      authorAvatar: "assets/images/farmer_greenharvest.jpg",
      timeAgo: "5 days ago",
      thumb: "assets/images/farmer_greenharvest.jpg",
      fullDescription: "Green Harvest has access to high-grade certified organic chili, coriander, and turmeric. We want to partner with seasoned culinary artisans or chefs to develop export-quality blended masalas with standardized recipes."
    },
    {
      id: "collab-4",
      title: "Bulk Honey Logistics & Jar Sourcing",
      subtitle: "Seeking dependable food-grade glass jar suppliers and interstate courier rates.",
      category: "Organic Products",
      type: "Seeking Partners",
      tag: "Logistics",
      location: "Bihar",
      authorName: "Suresh Yadav",
      authorAvatar: "assets/images/suresh_yadav.jpg",
      timeAgo: "1 week ago",
      thumb: "assets/images/suresh_yadav.jpg",
      fullDescription: "Looking to connect with packaging vendors who supply 250g and 500g hexagon glass jars at wholesale rates, plus logistics partners offering safe transport with low breakage."
    }
  ],

  discussions: [
    {
      id: "disc-1",
      authorName: "Ramesh Kumar",
      authorMeta: "Agriculture • Karnataka",
      authorAvatar: "assets/images/ramesh_kumar.jpg",
      timeAgo: "3 hours ago",
      title: "How do you find customers outside your district?",
      body: "We produce organic turmeric and other spices. Currently most of our sales are local. I would like to know how other rural entrepreneurs have reached customers in different states. Any advice or experiences would be really helpful!",
      tag: "Question",
      likes: 6,
      commentsCount: 8,
      comments: [
        {
          authorName: "Asha Devi",
          authorMeta: "Handicrafts • Uttar Pradesh",
          authorAvatar: "assets/images/artisan_asha.jpg",
          timeAgo: "2 hours ago",
          text: "Namaste Ramesh ji. We faced the same barrier initially! Two things worked wonders for us: participating in state government SARAS artisan fairs, and connecting with regional postal parcel services (India Post) for cost-effective interstate shipping."
        },
        {
          authorName: "Rahul Sharma",
          authorMeta: "Digital Services • Rajasthan",
          authorAvatar: "assets/images/digital_rahul.jpg",
          timeAgo: "1 hour ago",
          text: "Great question! Creating a simple WhatsApp Business catalog and listing your turmeric on ONDC (Open Network for Digital Commerce) allows buyers nationwide to discover you directly without high platform commissions."
        },
        {
          authorName: "Meera Patil",
          authorMeta: "Food Products • Maharashtra",
          authorAvatar: "assets/images/meera_patil.jpg",
          timeAgo: "35 mins ago",
          text: "Also try reaching out to organic retail stores in tier-1 cities like Bengaluru and Pune. Send them small trial sample boxes. Once they taste genuine farm quality, they place recurring monthly bulk orders."
        }
      ]
    }
  ],

  articles: [
    {
      id: "art-1",
      category: "Success Stories",
      title: "How we expanded our customer base through online marketplaces",
      authorName: "Meera Patil",
      authorCategory: "Food Products",
      authorAvatar: "assets/images/meera_patil.jpg",
      date: "June 10, 2024",
      image: "assets/images/packaging_spices.jpg",
      summary: "A step-by-step account of taking a home kitchen enterprise from selling 20 jars a week locally to dispatching 400+ food packages a month across three states."
    },
    {
      id: "art-2",
      category: "How-To Guides",
      title: "Simple ways to take better product photos using your phone",
      authorName: "Rahul Sharma",
      authorCategory: "Digital Services",
      authorAvatar: "assets/images/digital_rahul.jpg",
      date: "June 8, 2024",
      image: "assets/images/phone_photography.jpg",
      summary: "You don't need an expensive camera to showcase your crafts. Learn how to use morning window light, simple white background charts, and basic camera angles to make your products stand out."
    },
    {
      id: "art-3",
      category: "Success Stories",
      title: "Our journey from a small village business to national markets",
      authorName: "Asha Devi",
      authorCategory: "Handicrafts",
      authorAvatar: "assets/images/artisan_asha.jpg",
      date: "June 5, 2024",
      image: "assets/images/village_journey.jpg",
      summary: "How an initiative starting with five neighborhood women grew into a self-reliant artisan collective recognized at national craft melas."
    },
    {
      id: "art-4",
      category: "Business Tips",
      title: "Packaging essentials: protecting fragile craft goods in transit",
      authorName: "Suresh Yadav",
      authorCategory: "Organic Products",
      authorAvatar: "assets/images/suresh_yadav.jpg",
      date: "May 25, 2024",
      image: "assets/images/hero_entrepreneur.jpg",
      summary: "Practical techniques using corrugated fluting, shredded recycled paper, and honeycomb sleeves to minimize transit breakage."
    },
    {
      id: "art-5",
      category: "Industry Insights",
      title: "Understanding organic certification for smallholder farmers",
      authorName: "Green Harvest",
      authorCategory: "Agriculture",
      authorAvatar: "assets/images/farmer_greenharvest.jpg",
      date: "May 18, 2024",
      image: "assets/images/farmer_greenharvest.jpg",
      summary: "A plain-language breakdown of PGS-India and Jaivik Bharat certifications, cluster group guarantees, and timeline expectations."
    }
  ]
};

// Export to window
window.UDYAM_DATA = UDYAM_DATA;
