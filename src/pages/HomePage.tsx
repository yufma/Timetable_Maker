import React from 'react'
import { useWishlist } from '../contexts/WishlistContext'
import WelcomeSection from '../components/WelcomeSection'
import ActionSection from '../components/ActionSection'
import HowToSection from '../components/HowToSection'

const HomePage: React.FC = () => {
  const { wishlist } = useWishlist()

  return (
    <main className="main-content">
      <WelcomeSection />
      <ActionSection wishlistCount={wishlist.length} />
      <HowToSection />
    </main>
  )
}

export default HomePage

