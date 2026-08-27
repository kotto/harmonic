package com.vitalka.app;

import android.graphics.Bitmap;
import android.os.Bundle;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import com.getcapacitor.BridgeActivity;
import com.getcapacitor.community.speechrecognition.SpeechRecognition;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(SpeechRecognition.class);
        super.onCreate(savedInstanceState);

        getBridge().getWebView().post(() -> {
            WebView wv = getBridge().getWebView();
            if (wv == null) return;

            WebViewClient original = wv.getWebViewClient();

            wv.setWebViewClient(new WebViewClient() {
                @Override
                public boolean shouldOverrideUrlLoading(WebView view, String url) {
                    return fixAndRedirect(view, url) || original.shouldOverrideUrlLoading(view, url);
                }

                @Override
                public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                    String url = request.getUrl().toString();
                    return fixAndRedirect(view, url) || original.shouldOverrideUrlLoading(view, request);
                }

                @Override
                public void onPageStarted(WebView view, String url, Bitmap favicon) {
                    original.onPageStarted(view, url, favicon);
                }

                @Override
                public void onPageFinished(WebView view, String url) {
                    original.onPageFinished(view, url);
                    // Injection JS de sécurité + fix KA_PLATFORM
                    injectFixJS(view);
                }
            });

            // Fix immédiat
            wv.evaluateJavascript(getFixJS(), null);
        });
    }

    /**
     * Intercepte les navigations vers des fichiers .html inexistants sur le serveur
     * et les redirige vers les bonnes routes REST /vital/{role}.
     */
    private boolean fixAndRedirect(WebView view, String url) {
        if (url == null) return false;

        // Définir les corrections : fichier.html → route correcte
        String[][] redirects = {
            {"ka_admin.html",         "/vital/launcher"},
            {"ka_diaspora_shop.html",  "/vital/launcher"},
            {"ka_pharmacien.html",     "/vital/pharmacien"},
            {"ka_solidarite.html",     "/vital/solidarite"},
            {"ka_laboratoire.html",    "/vital/launcher"},
            {"ka_launcher.html",       "/vital/launcher"},
            {"vital_ka.html",          "/vital/medecin"},  // vital_ka.html = espace médecin
        };

        for (String[] r : redirects) {
            if (url.contains(r[0])) {
                String base = "http://158.178.215.219";
                view.loadUrl(base + r[1]);
                return true; // intercepté, redirigé
            }
        }

        return false; // laisser passer normalement
    }

    private void injectFixJS(WebView wv) {
        // Fix JS : redéfinit openApp APRÈS que ka_platform.js a fini de charger
        wv.evaluateJavascript(getFixJS(), null);
    }

    private String getFixJS() {
        return "(function(){ " +
            "  function fix(){ " +
            "    if(typeof KA_PLATFORM !== 'undefined'){ " +
            "      KA_PLATFORM.openApp = function(role){ " +
            "        var m = {medecin:'/vital/medecin',patient:'/vital/patient',pharmacien:'/vital/pharmacien',solidarite:'/vital/solidarite'}; " +
            "        window.location.href = m[role] || '/vital/launcher'; " +
            "      }; " +
            "    } " +
            "    window.open = function(url){ if(url) window.location.href = url; return window; }; " +
            "  } " +
            "  fix(); " +
            // Réessayer 3 fois pour dominer ka_platform.js s'il arrive après
            "  setTimeout(fix, 500); " +
            "  setTimeout(fix, 1500); " +
            "  setTimeout(fix, 3000); " +
            "})();";
    }
}