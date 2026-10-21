import { Container } from '@/components/ui';
import { NotFoundPage, ProductListPage } from '@/pages';
import { ProductPage } from '@/pages/ProductPage';
import { Route, Switch } from 'wouter';

function App() {
  return (
    <div className="h-screen flex flex-col">
      {/* TODO: сверстать header */}
      <header className="bg-secondary text-primary mb-5">
        <Container className="py-2">Это будущий Header</Container>
      </header>

      <Switch>
        <Route path="/">
          <ProductListPage />
        </Route>
        <Route path="/product/:code" nest>
          <ProductPage />
        </Route>

        <Route>
          <NotFoundPage />
        </Route>
      </Switch>
    </div>
  );
}

export default App;
