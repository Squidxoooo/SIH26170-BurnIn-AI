import logo from "@/assets/burnin-logo.png.asset.json";

export function LogoMark({ className = "h-10 w-10" }: { className?: string }) {
  return (
    <img
      src={logo.url}
      alt="BurnIn-AI logo"
      className={`${className} rounded-md object-cover object-center`}
      style={{ objectPosition: "50% 38%" }}
    />
  );
}

export function LogoFull({ className = "" }: { className?: string }) {
  return <img src={logo.url} alt="BurnIn-AI — Detect, Predict, Ensure" className={className} />;
}

export function LogoLockup() {
  return (
    <div className="flex items-center gap-3">
      <LogoMark className="h-9 w-9" />
      <div className="leading-none">
        <div className="text-sm font-semibold tracking-tight text-foreground">BurnIn-AI</div>
        <div className="mt-1 font-mono text-[10px] tracking-[0.2em] text-muted-foreground">
          DETECT · PREDICT · ENSURE
        </div>
      </div>
    </div>
  );
}
