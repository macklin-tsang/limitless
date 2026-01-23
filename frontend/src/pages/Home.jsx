import React from 'react';
import { Link } from 'react-router-dom';

function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-felt-green to-felt-green-light flex flex-col items-center justify-center p-4">
      <div className="text-center">
        <h1 className="text-5xl font-bold text-white mb-4">
          Limitless Poker AI
        </h1>
        <p className="text-xl text-gray-200 mb-8 max-w-lg">
          Play against intelligent poker agents and improve your game.
          Test your skills against TAG, LAG, and other AI strategies.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            to="/play"
            className="px-8 py-4 bg-yellow-500 hover:bg-yellow-400 text-gray-900 font-bold text-lg rounded-lg shadow-lg transition-all transform hover:scale-105"
          >
            Play vs Agent
          </Link>
          <Link
            to="/simulation"
            className="px-8 py-4 bg-white/10 hover:bg-white/20 text-white font-bold text-lg rounded-lg shadow-lg border border-white/30 transition-all transform hover:scale-105"
          >
            Run Simulation
          </Link>
        </div>
      </div>

      <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl">
        <FeatureCard
          title="Smart Agents"
          description="Face off against multiple AI personalities: tight-aggressive, loose-aggressive, and more."
        />
        <FeatureCard
          title="Real Strategy"
          description="Agents use position, pot odds, and hand strength to make decisions like real players."
        />
        <FeatureCard
          title="Track Progress"
          description="View statistics, hand histories, and performance metrics to improve your game."
        />
      </div>
    </div>
  );
}

function FeatureCard({ title, description }) {
  return (
    <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6 border border-white/20">
      <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>
      <p className="text-gray-300">{description}</p>
    </div>
  );
}

export default Home;
