import { createRoutesFromElements, Route } from "react-router";
import Root from "./root";
import Home from "./routes/home";
import Dashboard from "./routes/dashboard";
import Account from "./routes/account";
import SellerLogin from "./routes/seller/login";
import SellerForgotPassword from "./routes/seller/forgot-password";
import SellerResetPassword from "./routes/seller/reset-password";
import SellerSubmitShipment from "./routes/seller/submit-shipment";
import PartnerLogin from "./routes/partner/login";
import PartnerForgotPassword from "./routes/partner/forgot-password";
import PartnerResetPassword from "./routes/partner/reset-password";
import PartnerUpdateShipment from "./routes/partner/update-shipment";
import { ErrorPage } from "./components/error-page";

// Export routes array from createRoutesFromElements
const routes = createRoutesFromElements(
  <Route element={<Root />} errorElement={<ErrorPage />}>
    <Route index element={<Home />} />
    <Route path="/dashboard" element={<Dashboard />} errorElement={<ErrorPage />} />
    <Route path="/account" element={<Account />} errorElement={<ErrorPage />} />
    <Route path="/submit-shipment" element={<SellerSubmitShipment />} errorElement={<ErrorPage />} />
    <Route path="/update-shipment" element={<PartnerUpdateShipment />} errorElement={<ErrorPage />} />
    <Route path="/seller/login" element={<SellerLogin />} errorElement={<ErrorPage />} />
    <Route path="/seller/forgot-password" element={<SellerForgotPassword />} errorElement={<ErrorPage />} />
    <Route path="/seller/reset-password" element={<SellerResetPassword />} errorElement={<ErrorPage />} />
    <Route path="/partner/login" element={<PartnerLogin />} errorElement={<ErrorPage />} />
    <Route path="/partner/forgot-password" element={<PartnerForgotPassword />} errorElement={<ErrorPage />} />
    <Route path="/partner/reset-password" element={<PartnerResetPassword />} errorElement={<ErrorPage />} />
    {/* Catch-all route for 404 */}
    <Route path="*" element={<ErrorPage />} />
  </Route>
);

export default routes;
