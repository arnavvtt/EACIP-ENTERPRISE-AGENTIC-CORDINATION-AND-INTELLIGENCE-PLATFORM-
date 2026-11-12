import { Link, useLocation } from "react-router-dom";
import { ChevronRight, Moon, Sun, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/lib/theme";

export function Topbar() {
  const { pathname } = useLocation();
  const { theme, toggle } = useTheme();

  const segments = pathname.split("/").filter(Boolean);

  return (
    <header className="h-16 border-b border-border bg-background/95 backdrop-blur sticky top-0 z-10">
      <div className="flex h-full items-center px-6 gap-4">
        <nav className="flex items-center gap-1 text-sm flex-1 min-w-0">
          <Link to="/" className="text-muted-foreground hover:text-foreground shrink-0">
            Home
          </Link>
          {segments.map((seg, i) => {
            const to = "/" + segments.slice(0, i + 1).join("/");
            const isLast = i === segments.length - 1;
            return (
              <div key={to} className="flex items-center gap-1 min-w-0">
                <ChevronRight className="w-3 h-3 text-muted-foreground shrink-0" />
                <Link
                  to={to}
                  className={
                    isLast
                      ? "text-foreground font-medium truncate"
                      : "text-muted-foreground hover:text-foreground truncate"
                  }
                >
                  {seg.charAt(0).toUpperCase() + seg.slice(1)}
                </Link>
              </div>
            );
          })}
        </nav>

        <Button variant="ghost" size="icon" onClick={toggle} className="lg:hidden shrink-0">
          {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </Button>

        <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center shrink-0">
          <User className="w-4 h-4 text-muted-foreground" />
        </div>
      </div>
    </header>
  );
}