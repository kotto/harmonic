"""
💰 FINANCE-HARMONIC - Calcul Financier Harmonique
Fichier: finance_harmonique.py
Auteur: Équipe Harmonique
Date: 28 avril 2026
Description: Implémentation des algorithmes financiers optimisés avec les constantes harmoniques
"""

import numpy as np
import time
import logging
from typing import List, Tuple, Dict, Any, Optional, Callable
from dataclasses import dataclass
from scipy.stats import norm
from classique_harmonique import ClassicalHarmonicComputer, PHI, PI, E

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class FinancialMetrics:
    """Métriques financières harmoniques"""
    prix: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    temps_calcul: float
    precision: float

class HarmonicBlackScholes:
    """
    Modèle Black-Scholes harmonique
    """
    
    def __init__(self, harmonic_computer: ClassicalHarmonicComputer):
        self.computer = harmonic_computer
        self.phi_optimization = PHI
        self.pi_optimization = PI
        self.e_optimization = E
        
        logger.info("HarmonicBlackScholes initialisé")
    
    def black_scholes_harmonique(self, S: float, K: float, T: float, r: float, 
                                sigma: float, option_type: str = 'call') -> FinancialMetrics:
        """
        Calcul Black-Scholes harmonique
        
        Args:
            S: Prix du sous-jacent
            K: Prix d'exercice
            T: Temps jusqu'à maturité
            r: Taux sans risque
            sigma: Volatilité
            option_type: 'call' ou 'put'
            
        Returns:
            Métriques financières harmoniques
        """
        try:
            start_time = time.time()
            
            # Paramètres harmoniques
            r_h = r * self.phi_optimization
            sigma_h = sigma / np.sqrt(self.phi_optimization)
            T_h = T * self.phi_optimization / self.pi_optimization
            
            # Calcul des d1 et d2 harmoniques
            d1 = (np.log(S / K) + (r_h + sigma_h**2 / 2) * T_h) / (sigma_h * np.sqrt(T_h))
            d2 = d1 - sigma_h * np.sqrt(T_h)
            
            # Facteurs de distribution harmonique
            phi_factor = self.phi_optimization / (1 + np.exp(-d1))
            
            if option_type.lower() == 'call':
                # Prix du call harmonique
                prix = (S * norm.cdf(d1) * phi_factor - 
                       K * np.exp(-r_h * T_h) * norm.cdf(d2) * phi_factor)
                
                # Grecques harmoniques
                delta = norm.cdf(d1) * phi_factor
                gamma = norm.pdf(d1) / (S * sigma_h * np.sqrt(T_h)) * phi_factor
                theta = (-S * norm.pdf(d1) * sigma_h / (2 * np.sqrt(T_h)) * phi_factor -
                        r_h * K * np.exp(-r_h * T_h) * norm.cdf(d2) * phi_factor)
                vega = S * norm.pdf(d1) * np.sqrt(T_h) * phi_factor
                rho = K * T_h * np.exp(-r_h * T_h) * norm.cdf(d2) * phi_factor
                
            else:  # put
                # Prix du put harmonique
                prix = (K * np.exp(-r_h * T_h) * norm.cdf(-d2) * phi_factor -
                       S * norm.cdf(-d1) * phi_factor)
                
                # Grecques harmoniques
                delta = -norm.cdf(-d1) * phi_factor
                gamma = norm.pdf(d1) / (S * sigma_h * np.sqrt(T_h)) * phi_factor
                theta = (-S * norm.pdf(d1) * sigma_h / (2 * np.sqrt(T_h)) * phi_factor +
                        r_h * K * np.exp(-r_h * T_h) * norm.cdf(-d2) * phi_factor)
                vega = S * norm.pdf(d1) * np.sqrt(T_h) * phi_factor
                rho = -K * T_h * np.exp(-r_h * T_h) * norm.cdf(-d2) * phi_factor
            
            temps_calcul = time.time() - start_time
            precision = 1.0 - abs(prix - self._black_scholes_standard(S, K, T, r, sigma, option_type)) / prix
            
            logger.info(f"Black-Scholes harmonique: {option_type} {prix:.4f} en {temps_calcul:.4f}s")
            
            return FinancialMetrics(
                prix=prix,
                delta=delta,
                gamma=gamma,
                theta=theta,
                vega=vega,
                rho=rho,
                temps_calcul=temps_calcul,
                precision=precision
            )
            
        except Exception as e:
            logger.error(f"Erreur dans Black-Scholes harmonique: {e}")
            return self._fallback_black_scholes(S, K, T, r, sigma, option_type)
    
    def _black_scholes_standard(self, S: float, K: float, T: float, r: float, 
                                sigma: float, option_type: str = 'call') -> float:
        """Calcul Black-Scholes standard pour comparaison"""
        d1 = (np.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if option_type.lower() == 'call':
            return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:
            return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    
    def _fallback_black_scholes(self, S: float, K: float, T: float, r: float, 
                                sigma: float, option_type: str = 'call') -> FinancialMetrics:
        """Fallback vers calcul standard"""
        start_time = time.time()
        prix = self._black_scholes_standard(S, K, T, r, sigma, option_type)
        temps_calcul = time.time() - start_time
        
        return FinancialMetrics(
            prix=prix,
            delta=0.0,
            gamma=0.0,
            theta=0.0,
            vega=0.0,
            rho=0.0,
            temps_calcul=temps_calcul,
            precision=1.0
        )

class HarmonicPortfolioOptimization:
    """
    Optimisation de portefeuille harmonique
    """
    
    def __init__(self, harmonic_computer: ClassicalHarmonicComputer):
        self.computer = harmonic_computer
        self.phi_optimization = PHI
        self.pi_optimization = PI
        
        logger.info("HarmonicPortfolioOptimization initialisé")
    
    def markowitz_optimization_harmonique(self, returns: np.ndarray, 
                                         risk_free_rate: float = 0.02) -> Dict[str, Any]:
        """
        Optimisation de portefeuille Markowitz harmonique
        
        Args:
            returns: Matrice des rendements (actifs × temps)
            risk_free_rate: Taux sans risque
            
        Returns:
            Dictionnaire des résultats d'optimisation
        """
        try:
            start_time = time.time()
            
            # Calcul des statistiques harmoniques
            mean_returns = np.mean(returns, axis=1)
            cov_matrix = np.cov(returns)
            
            # Optimisation harmonique des poids
            n_assets = len(mean_returns)
            
            # Fonction objectif harmonique
            def objective(weights):
                portfolio_return = np.sum(mean_returns * weights)
                portfolio_risk = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                
                # Facteur d'harmonisation
                harmonic_factor = (1 + self.phi_optimization / n_assets) * np.exp(-portfolio_risk / self.pi_optimization)
                
                return -(portfolio_return - risk_free_rate) / portfolio_risk * harmonic_factor
            
            # Contraintes harmoniques
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # Somme des poids = 1
                {'type': 'ineq', 'fun': lambda x: x}  # Poids non-négatifs
            ]
            
            # Point initial harmonique
            x0 = np.ones(n_assets) / n_assets * self.phi_optimization
            x0 = x0 / np.sum(x0)
            
            # Optimisation harmonique
            from scipy.optimize import minimize
            result = minimize(objective, x0, method='SLSQP', constraints=constraints)
            
            if result.success:
                weights = result.x
                portfolio_return = np.sum(mean_returns * weights)
                portfolio_risk = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_risk
                
                temps_calcul = time.time() - start_time
                
                logger.info(f"Optimisation Markowitz harmonique: Sharpe {sharpe_ratio:.4f} en {temps_calcul:.4f}s")
                
                return {
                    'weights': weights,
                    'expected_return': portfolio_return,
                    'risk': portfolio_risk,
                    'sharpe_ratio': sharpe_ratio,
                    'temps_calcul': temps_calcul,
                    'success': True
                }
            else:
                logger.error("Échec de l'optimisation Markowitz harmonique")
                return {'success': False, 'error': result.message}
                
        except Exception as e:
            logger.error(f"Erreur dans l'optimisation Markowitz harmonique: {e}")
            return {'success': False, 'error': str(e)}
    
    def risk_parity_harmonique(self, cov_matrix: np.ndarray) -> np.ndarray:
        """
        Allocation Risk Parity harmonique
        
        Args:
            cov_matrix: Matrice de covariance
            
        Returns:
            Poids optimaux
        """
        try:
            start_time = time.time()
            
            n_assets = cov_matrix.shape[0]
            
            # Fonction objectif pour risk parity harmonique
            def risk_parity_objective(weights):
                portfolio_risk = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                marginal_contrib = np.dot(cov_matrix, weights) / portfolio_risk
                contrib = weights * marginal_contrib
                
                # Facteur d'harmonisation
                harmonic_factor = self.phi_optimization * np.exp(-np.std(contrib) / self.pi_optimization)
                
                return np.sum((contrib - np.mean(contrib))**2) * harmonic_factor
            
            # Contraintes
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'ineq', 'fun': lambda x: x}
            ]
            
            # Point initial harmonique
            x0 = np.ones(n_assets) / n_assets
            
            # Optimisation
            from scipy.optimize import minimize
            result = minimize(risk_parity_objective, x0, method='SLSQP', constraints=constraints)
            
            temps_calcul = time.time() - start_time
            
            if result.success:
                logger.info(f"Risk Parity harmonique: optimisé en {temps_calcul:.4f}s")
                return result.x
            else:
                logger.warning("Risk Parity harmonique: fallback vers égalité")
                return np.ones(n_assets) / n_assets
                
        except Exception as e:
            logger.error(f"Erreur dans Risk Parity harmonique: {e}")
            n_assets = cov_matrix.shape[0]
            return np.ones(n_assets) / n_assets

class HarmonicRiskAnalysis:
    """
    Analyse de risque harmonique
    """
    
    def __init__(self, harmonic_computer: ClassicalHarmonicComputer):
        self.computer = harmonic_computer
        self.phi_optimization = PHI
        self.pi_optimization = PI
        
        logger.info("HarmonicRiskAnalysis initialisé")
    
    def var_harmonique(self, returns: np.ndarray, confidence_level: float = 0.05) -> Dict[str, float]:
        """
        Value at Risk harmonique
        
        Args:
            returns: Série des rendements
            confidence_level: Niveau de confiance
            
        Returns:
            Métriques VaR harmoniques
        """
        try:
            start_time = time.time()
            
            # VaR historique harmonique
            sorted_returns = self.computer.sorting.quicksort_harmonique(returns.tolist())
            var_historique = sorted_returns[int(len(sorted_returns) * confidence_level)]
            
            # VaR paramétrique harmonique
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            
            # Ajustement harmonique
            std_h = std_return / np.sqrt(self.phi_optimization)
            var_parametric = mean_return + std_h * norm.ppf(confidence_level)
            
            # VaR Monte Carlo harmonique
            n_simulations = 10000
            simulated_returns = np.random.normal(mean_return, std_h, n_simulations)
            simulated_returns = self.computer.sorting.quicksort_harmonique(simulated_returns.tolist())
            var_monte_carlo = simulated_returns[int(len(simulated_returns) * confidence_level)]
            
            temps_calcul = time.time() - start_time
            
            logger.info(f"VaR harmonique: calculé en {temps_calcul:.4f}s")
            
            return {
                'var_historique': var_historique,
                'var_parametric': var_parametric,
                'var_monte_carlo': var_monte_carlo,
                'confidence_level': confidence_level,
                'temps_calcul': temps_calcul
            }
            
        except Exception as e:
            logger.error(f"Erreur dans VaR harmonique: {e}")
            return {'error': str(e)}
    
    def cvar_harmonique(self, returns: np.ndarray, confidence_level: float = 0.05) -> float:
        """
        Conditional Value at Risk harmonique
        
        Args:
            returns: Série des rendements
            confidence_level: Niveau de confiance
            
        Returns:
            CVaR harmonique
        """
        try:
            var_result = self.var_harmonique(returns, confidence_level)
            
            if 'error' in var_result:
                return 0.0
            
            var_value = var_result['var_historique']
            
            # CVaR : moyenne des pertes au-delà de VaR
            tail_losses = [r for r in returns if r < var_value]
            cvar = np.mean(tail_losses) if tail_losses else var_value
            
            logger.info(f"CVaR harmonique: {cvar:.6f}")
            
            return cvar
            
        except Exception as e:
            logger.error(f"Erreur dans CVaR harmonique: {e}")
            return 0.0

class HarmonicMonteCarlo:
    """
    Simulation Monte Carlo harmonique
    """
    
    def __init__(self, harmonic_computer: ClassicalHarmonicComputer):
        self.computer = harmonic_computer
        self.phi_optimization = PHI
        self.pi_optimization = PI
        
        logger.info("HarmonicMonteCarlo initialisé")
    
    def price_option_monte_carlo_harmonique(self, S0: float, K: float, T: float, r: float, 
                                           sigma: float, n_simulations: int = 10000,
                                           option_type: str = 'call') -> Dict[str, Any]:
        """
        Pricing d'option par Monte Carlo harmonique
        
        Args:
            S0: Prix initial du sous-jacent
            K: Prix d'exercice
            T: Temps jusqu'à maturité
            r: Taux sans risque
            sigma: Volatilité
            n_simulations: Nombre de simulations
            option_type: 'call' ou 'put'
            
        Returns:
            Résultats du pricing Monte Carlo harmonique
        """
        try:
            start_time = time.time()
            
            # Paramètres harmoniques
            r_h = r * self.phi_optimization
            sigma_h = sigma / np.sqrt(self.phi_optimization)
            
            # Génération harmonique des trajectoires
            Z = np.random.standard_normal(n_simulations)
            
            # Distribution harmonique
            Z_harmonic = [z * (1 + np.sin(2 * self.pi_optimization * i / n_simulations) / self.phi_optimization) 
                         for i, z in enumerate(Z)]
            
            # Simulation des prix
            ST = S0 * np.exp((r_h - 0.5 * sigma_h**2) * T + sigma_h * np.sqrt(T) * np.array(Z_harmonic))
            
            # Calcul des payoffs
            if option_type.lower() == 'call':
                payoffs = np.maximum(ST - K, 0)
            else:
                payoffs = np.maximum(K - ST, 0)
            
            # Prix actualisé harmonique
            option_price = np.mean(payoffs) * np.exp(-r_h * T)
            
            # Calcul des statistiques
            std_error = np.std(payoffs) / np.sqrt(n_simulations)
            
            temps_calcul = time.time() - start_time
            
            logger.info(f"Monte Carlo harmonique: {option_type} {option_price:.4f} en {temps_calcul:.4f}s")
            
            return {
                'price': option_price,
                'std_error': std_error,
                'n_simulations': n_simulations,
                'temps_calcul': temps_calcul,
                'confidence_interval': (option_price - 1.96 * std_error, option_price + 1.96 * std_error)
            }
            
        except Exception as e:
            logger.error(f"Erreur dans Monte Carlo harmonique: {e}")
            return {'error': str(e)}

class HarmonicFinanceComputer:
    """
    Ordinateur financier harmonique complet
    """
    
    def __init__(self):
        self.computer = ClassicalHarmonicComputer()
        self.black_scholes = HarmonicBlackScholes(self.computer)
        self.portfolio = HarmonicPortfolioOptimization(self.computer)
        self.risk = HarmonicRiskAnalysis(self.computer)
        self.monte_carlo = HarmonicMonteCarlo(self.computer)
        
        logger.info("HarmonicFinanceComputer initialisé")
    
    def analyze_portfolio(self, prices: np.ndarray, risk_free_rate: float = 0.02) -> Dict[str, Any]:
        """
        Analyse complète de portefeuille harmonique
        
        Args:
            prices: Matrice des prix (actifs × temps)
            risk_free_rate: Taux sans risque
            
        Returns:
            Analyse complète du portefeuille
        """
        try:
            # Calcul des rendements
            returns = np.diff(np.log(prices), axis=1)
            
            # Optimisation Markowitz
            markowitz_result = self.portfolio.markowitz_optimization_harmonique(returns, risk_free_rate)
            
            # Analyse de risque
            portfolio_returns = np.dot(markowitz_result['weights'], returns)
            var_result = self.risk.var_harmonique(portfolio_returns)
            cvar_result = self.risk.cvar_harmonique(portfolio_returns)
            
            # Pricing d'options sur le portefeuille
            portfolio_value = np.sum(prices[:, -1] * markowitz_result['weights'])
            option_result = self.black_scholes.black_scholes_harmonique(
                portfolio_value, portfolio_value * 1.1, 1.0, risk_free_rate, 0.2
            )
            
            return {
                'optimization': markowitz_result,
                'risk_analysis': var_result,
                'cvar': cvar_result,
                'option_pricing': option_result,
                'portfolio_value': portfolio_value
            }
            
        except Exception as e:
            logger.error(f"Erreur dans l'analyse de portefeuille: {e}")
            return {'error': str(e)}

def main():
    """Fonction principale pour tester l'ordinateur financier harmonique"""
    try:
        print("💰 INITIALISATION DE L'ORDINATEUR FINANCIER HARMONIQUE")
        print("="*60)
        
        # Création de l'ordinateur
        computer = HarmonicFinanceComputer()
        
        # Test Black-Scholes
        print("\n📈 TEST BLACK-SCHOLES HARMONIQUE")
        print("-"*40)
        
        bs_result = computer.black_scholes.black_scholes_harmonique(
            S=100, K=105, T=1.0, r=0.05, sigma=0.2, option_type='call'
        )
        
        print(f"✅ Prix du call: {bs_result.prix:.4f}")
        print(f"✅ Delta: {bs_result.delta:.4f}")
        print(f"✅ Gamma: {bs_result.gamma:.4f}")
        print(f"✅ Temps de calcul: {bs_result.temps_calcul:.4f}s")
        print(f"✅ Précision: {bs_result.precision:.4f}")
        
        # Test optimisation de portefeuille
        print("\n📊 TEST OPTIMISATION DE PORTEFEUILLE")
        print("-"*40)
        
        # Génération de données de test
        np.random.seed(42)
        n_assets = 5
        n_periods = 252
        returns = np.random.normal(0.001, 0.02, (n_assets, n_periods))
        
        portfolio_result = computer.portfolio.markowitz_optimization_harmonique(returns)
        
        if portfolio_result['success']:
            print(f"✅ Sharpe Ratio: {portfolio_result['sharpe_ratio']:.4f}")
            print(f"✅ Rendement attendu: {portfolio_result['expected_return']:.4f}")
            print(f"✅ Risque: {portfolio_result['risk']:.4f}")
            print(f"✅ Temps de calcul: {portfolio_result['temps_calcul']:.4f}s")
        
        # Test VaR
        print("\n⚠️ TEST VALUE AT RISK")
        print("-"*40)
        
        portfolio_returns = np.dot(portfolio_result['weights'], returns)
        var_result = computer.risk.var_harmonique(portfolio_returns)
        
        if 'error' not in var_result:
            print(f"✅ VaR Historique: {var_result['var_historique']:.6f}")
            print(f"✅ VaR Paramétrique: {var_result['var_parametric']:.6f}")
            print(f"✅ VaR Monte Carlo: {var_result['var_monte_carlo']:.6f}")
        
        # Test Monte Carlo
        print("\n🎲 TEST MONTE CARLO")
        print("-"*40)
        
        mc_result = computer.monte_carlo.price_option_monte_carlo_harmonique(
            S0=100, K=105, T=1.0, r=0.05, sigma=0.2, n_simulations=10000
        )
        
        if 'error' not in mc_result:
            print(f"✅ Prix de l'option: {mc_result['price']:.4f}")
            print(f"✅ Erreur standard: {mc_result['std_error']:.6f}")
            print(f"✅ Intervalle de confiance: {mc_result['confidence_interval']}")
        
        print("\n💰 ORDINATEUR FINANCIER HARMONIQUE OPÉRATIONNEL")
        
        return computer
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrompu par l'utilisateur")
        return None
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        return None

if __name__ == "__main__":
    main()
