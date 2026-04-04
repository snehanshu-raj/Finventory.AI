export default function Onboarding() {
  return (
    <div className="min-h-screen bg-bg flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-text mb-4">Onboarding</h1>
        <p className="text-muted mb-8">TEST COMPONENT - If you see this, routing works</p>
        <input type="text" placeholder="Name" className="block mb-4 w-64 p-2 rounded bg-surface text-text border border-border" />
        <input type="email" placeholder="Email" className="block mb-4 w-64 p-2 rounded bg-surface text-text border border-border" />
        <button className="bg-sky-500 text-white px-6 py-2 rounded">Submit</button>
      </div>
    </div>
  );
}
