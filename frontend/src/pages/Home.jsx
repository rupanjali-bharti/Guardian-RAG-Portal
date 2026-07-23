import Navbar from '../components/Navbar';
import Hero from '../components/Hero';
import Metrics from '../components/Metrics';
import Workflow from '../components/Workflow';
import Features from '../components/Features';
import CallToAction from '../components/CallToAction';

export default function Home() {
  return (
    <>
      <Navbar />
      <Hero />
      <Metrics />
      <Workflow />
      <Features />
      <CallToAction />
    </>
  );
}