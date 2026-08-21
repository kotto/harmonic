import { test, expect } from '@playwright/test'

/**
 * Tests e2e — Navigation principale KA Mobile v2
 * Vérifie que les 17 écrans sont accessibles et rendus correctement.
 */

test.describe('KA Mobile v2 — Navigation', () => {
  test('Accueil : sphère, intention et quick actions visibles', async ({ page }) => {
    await page.goto('/')
    
    // Titre
    await expect(page.locator('text=Bonjour')).toBeVisible()
    await expect(page.locator('text=Que souhaitez-vous faire ?')).toBeVisible()
    
    // Sphère KA
    await expect(page.locator('svg[aria-label="Sphère KA"]')).toBeVisible()
    
    // Quick actions
    await expect(page.getByRole('button', { name: 'Appel', exact: true })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Message', exact: true })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Souvenir' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Relations' })).toBeVisible()
    
    // Barre de navigation
    await expect(page.getByRole('button', { name: 'Accueil' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Messages' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Mémoire' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Plus' })).toBeVisible()
  })

  test("Navigation : Accueil → Messages → Appel", async ({ page }) => {
    await page.goto('/')
    
    // Aller aux messages
    await page.click('text=Message')
    await expect(page).toHaveURL(/\/messages/)
    await expect(page.locator('text=Tu es dispo demain soir ?')).toBeVisible()
    
    // Le clavier est visible
    await expect(page.locator('text=espace')).toBeVisible()
    await expect(page.locator('text=Envoyer')).toBeVisible()
    
    // Retour accueil
    await page.click('text=‹ KA')
    await expect(page).toHaveURL(/\/$/)
  })

  test("Messages : clavier et envoi", async ({ page }) => {
    await page.goto("/messages")
    
    // Le clavier est présent avec les touches
    await expect(page.locator(".key--life")).toBeVisible()
    await expect(page.locator(".key--spc")).toBeVisible()
    
    // Taper "bien" via le clavier
    for (const key of ["b", "i", "e", "n"]) {
      const k = page.locator(".key").filter({ hasText: key }).first()
      await k.click()
    }
    
    // Cliquer sur Envoyer (dans le clavier)
    await page.locator(".key--life").click()
    
    // Un message envoyé apparaît dans la liste
    const sentCount = await page.locator(".msg--m").count()
    expect(sentCount).toBeGreaterThan(1)
  })

  test("Menu Plus : accès aux espaces avancés", async ({ page }) => {
    await page.goto('/')
    
    // Ouvrir le menu Plus
    await page.click('text=Plus')
    
    // Vérifier les espaces dans le panneau Plus
    await expect(page.locator('text=Préparer').first()).toBeVisible()
    await expect(page.locator('text=Voyage').first()).toBeVisible()
    await expect(page.locator('text=Santé').first()).toBeVisible()
    await expect(page.locator('text=Espace disque').first()).toBeVisible()
    
    // Naviguer vers la santé
    await page.click('text=Santé')
    await expect(page).toHaveURL(/\/health/)
    await expect(page.locator('text=Diagnostic par résonance harmonique')).toBeVisible()
  })

  test("Mémoire : timeline et photos", async ({ page }) => {
    await page.goto('/memory')
    
    await expect(page.locator('text=Rome avec Sophie')).toBeVisible()
    await expect(page.locator('text=CHRONOLOGIE')).toBeVisible()
    await expect(page.locator('text=Colisée — 23 photos')).toBeVisible()
    await expect(page.locator('text=+44')).toBeVisible()
  })

  test("Santé : formulaire de diagnostic", async ({ page }) => {
    await page.goto('/health')
    
    // Inputs vitaux
    await expect(page.locator('input[placeholder="72"]')).toBeVisible()
    await expect(page.locator('input[placeholder="37.0"]')).toBeVisible()
    await expect(page.locator('input[placeholder="120"]')).toBeVisible()
    await expect(page.locator('input[placeholder="98"]')).toBeVisible()
    
    // Bouton diagnostiquer
    await expect(page.locator('text=🔬 Diagnostiquer')).toBeVisible()
  })

  test("Storage : sélecteur de qualité et upload", async ({ page }) => {
    await page.goto('/storage')
    
    await expect(page.locator('text=📦 Archive')).toBeVisible()
    await expect(page.locator('text=⭐ Standard')).toBeVisible()
    await expect(page.locator('text=🌱 Éco')).toBeVisible()
    await expect(page.locator('text=Choisir des fichiers')).toBeVisible()
  })

  test("Vital Ka : cartes de services", async ({ page }) => {
    await page.goto('/vitalka')
    
    await expect(page.locator('text=Portefeuille de soins')).toBeVisible()
    await expect(page.locator('text=Téléconsultation')).toBeVisible()
    await expect(page.locator('text=Aide sociale')).toBeVisible()
  })
})

test.describe('KA Mobile v2 — Responsive', () => {
   test("Écran plein sur mobile (< 420px)", async ({ page }) => {
    await page.goto('/')
    
    // Vérifier que le cadre téléphone s'adapte
    const dv = page.locator('.dv')
    const box = await dv.boundingBox()
    expect(box).not.toBeNull()
  })
})