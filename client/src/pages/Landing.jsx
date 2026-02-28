import { useNavigate } from "react-router-dom";

const Landing = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Navbar */}
      <nav className="flex items-center justify-between px-8 py-5 border-b border-gray-800">
        <div className="text-2xl font-bold text-blue-400">💊 RxShield</div>
        <button
          onClick={() => navigate("/login")}
          className="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded-lg font-medium transition-colors"
        >
          Login
        </button>
      </nav>

      {/* Hero */}
      <div className="flex flex-col items-center justify-center text-center px-4 py-24">
        <div className="bg-blue-600/20 text-blue-400 border border-blue-600/40 rounded-full px-4 py-1 text-sm mb-6">
          AI-Powered Healthcare Safety
        </div>
        <h1 className="text-6xl font-bold mb-6 leading-tight">
          Stop Prescription
          <br />
          <span className="text-blue-400">Errors Before They Happen</span>
        </h1>
        <p className="text-gray-400 text-xl max-w-2xl mb-10">
          RxShield uses AI to detect drug-drug interactions, dosage anomalies,
          LASA confusion, and indication mismatches — instantly.
        </p>
        <button
          onClick={() => navigate("/login")}
          className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-10 py-4 rounded-xl text-lg transition-colors"
        >
          Get Started →
        </button>
      </div>

      {/* Feature Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 px-8 pb-16 max-w-6xl mx-auto">
        {[
          {
            icon: "⚠️",
            title: "Drug Interactions",
            desc: "Detects dangerous drug combos like Aspirin + Warfarin",
          },
          {
            icon: "💊",
            title: "Dosage Anomaly",
            desc: "ML flags abnormal dosages for any drug/age combo",
          },
          {
            icon: "🔤",
            title: "LASA Detection",
            desc: "Catches look-alike/sound-alike drug confusion",
          },
          {
            icon: "📋",
            title: "Indication Match",
            desc: "Ensures drug matches patient diagnosis",
          },
        ].map((card, i) => (
          <div
            key={i}
            className="bg-gray-900 border border-gray-800 rounded-xl p-6 hover:border-blue-700 transition-colors"
          >
            <div className="text-3xl mb-3">{card.icon}</div>
            <h3 className="text-white font-semibold text-lg mb-2">
              {card.title}
            </h3>
            <p className="text-gray-400 text-sm">{card.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Landing;
