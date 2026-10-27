import { Header } from '@/components/Header';
import { NotFoundPage, ProductListPage, ProductPage } from '@/pages';
import { Route, Switch } from 'wouter';

function App() {
  return (
    <div className="h-screen flex flex-col">
      <Header />

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
