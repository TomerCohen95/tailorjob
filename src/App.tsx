import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { CVParsingProvider } from "@/contexts/CVParsingContext";
import { ParsingToast } from "@/components/cv/ParsingToast";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import UploadCV from "./pages/UploadCV";
import CVPreview from "./pages/CVPreview";
import Jobs from "./pages/Jobs";
import AddJob from "./pages/AddJob";
import TailorCV from "./pages/TailorCV";
import Pricing from "./pages/Pricing";
import Account from "./pages/Account";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <CVParsingProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <ParsingToast />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/upload-cv" element={<UploadCV />} />
            <Route path="/cv-preview" element={<CVPreview />} />
            <Route path="/cv/:id" element={<CVPreview />} />
            <Route path="/jobs" element={<Jobs />} />
            <Route path="/jobs/add" element={<AddJob />} />
            <Route path="/jobs/:id/tailor" element={<TailorCV />} />
            <Route path="/pricing" element={<Pricing />} />
            <Route path="/account" element={<Account />} />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </CVParsingProvider>
  </QueryClientProvider>
);

export default App;
